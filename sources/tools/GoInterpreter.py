import subprocess
import os, sys
import tempfile
import re

if __name__ == "__main__": # if running as a script for individual testing
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sources.tools.tools import Tools
from sources.tools.safety import is_any_unsafe
from sources.exceptions import SafetyCheckError, ToolExecutionError

class GoInterpreter(Tools):
    """
    This class is a tool to allow execution of Go code.
    """
    def __init__(self):
        super().__init__()
        self.tag = "go"
        self.name = "Go Interpreter"
        self.description = "This tool allows you to execute Go code."
        self.safety_enabled = True

    def execute(self, codes: list[str], safety: bool = True) -> str:
        """
        Execute Go code by compiling and running it with safety checks.
        
        Args:
            codes: List of Go code blocks to execute
            safety: If True, validate code for unsafe operations
            
        Returns:
            Execution output or error message
        """
        output = ""
        code = '\n'.join(codes) if isinstance(codes, list) else codes

        # Safety check: detect potentially dangerous Go code patterns
        if safety:
            dangerous_patterns = [
                'exec.Command', 'os.Remove', 'os.RemoveAll', 'syscall.',
                'net/http', 'http.Get', 'http.Post',
                'rm -rf', 'chmod', 'chown'
            ]
            for pattern in dangerous_patterns:
                if pattern in code:
                    self.logger.warning(f"Safety check detected potentially unsafe Go code: {pattern}")
                    # Note: We allow most Go code but warn on system-level operations
                    if 'os.Remove' in pattern or 'syscall' in pattern:
                        if self.safety_enabled:
                            return f"[Safety Warning] Potentially unsafe Go code detected: '{pattern}'. Execution aborted."

        if safety and input("Execute code? y/n ") != "y":
            return "Code rejected by user."

        with tempfile.TemporaryDirectory() as tmpdirname:
            source_file = os.path.join(tmpdirname, "temp.go")
            exec_file = os.path.join(tmpdirname, "temp")
            with open(source_file, 'w') as f:
                f.write(code)

            try:
                env = os.environ.copy()
                env["GO111MODULE"] = "off"
                compile_command = ["go", "build", "-o", exec_file, source_file]
                compile_result = subprocess.run(
                    compile_command,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    env=env
                )

                if compile_result.returncode != 0:
                    self.logger.error(f"Compilation failed: {compile_result.stderr}")
                    return f"Compilation failed: {compile_result.stderr}"

                run_command = [exec_file]
                run_result = subprocess.run(
                    run_command,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if run_result.returncode != 0:
                    self.logger.error(f"Execution failed: {run_result.stderr}")
                    return f"Execution failed: {run_result.stderr}"
                output = run_result.stdout
                self.logger.info(f"Go code executed successfully")

            except subprocess.TimeoutExpired as e:
                self.logger.error(f"Execution timed out: {str(e)}")
                return f"Execution timed out: {str(e)}"
            except FileNotFoundError:
                self.logger.error("'go' not found")
                return "Error: 'go' not found. Ensure Go is installed and in PATH."
            except Exception as e:
                self.logger.error(f"Code execution failed: {str(e)}")
                return f"Code execution failed: {str(e)}"

        return output

    def interpreter_feedback(self, output: str) -> str:
        """
        Provide feedback based on the output of the code execution
        """
        if self.execution_failure_check(output):
            feedback = f"[failure] Error in execution:\n{output}"
        else:
            feedback = "[success] Execution success, code output:\n" + output
        return feedback

    def execution_failure_check(self, feedback: str) -> bool:
        """
        Check if the code execution failed.
        """
        error_patterns = [
            r"error",
            r"failed",
            r"traceback",
            r"invalid",
            r"exception",
            r"syntax",
            r"panic",
            r"undefined",
            r"cannot"
        ]
        combined_pattern = "|".join(error_patterns)
        if re.search(combined_pattern, feedback, re.IGNORECASE):
            return True
        return False

if __name__ == "__main__":
    codes = [
"""
package main
import "fmt"

func hello() {
    fmt.Println("Hello, World!")
}
""",
"""
func main() {
    hello()
}
"""
    ]
    g = GoInterpreter()
    print(g.execute(codes))
