import subprocess
import os, sys
import tempfile
import re

if __name__ == "__main__": # if running as a script for individual testing
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sources.tools.tools import Tools
from sources.tools.safety import is_any_unsafe
from sources.exceptions import SafetyCheckError, ToolExecutionError

class CInterpreter(Tools):
    """
    This class is a tool to allow agent for C code execution
    """
    def __init__(self):
        super().__init__()
        self.tag = "c"
        self.name = "C Interpreter"
        self.description = "This tool allows the agent to execute C code."
        self.safety_enabled = True

    def execute(self, codes: list[str], safety: bool = True) -> str:
        """
        Execute C code by compiling and running it with safety checks.
        
        Args:
            codes: List of C code blocks to execute
            safety: If True, validate code for unsafe operations
            
        Returns:
            Execution output or error message
        """
        output = ""
        code = '\n'.join(codes) if isinstance(codes, list) else codes

        # Safety check: detect potentially dangerous C code patterns
        if safety:
            dangerous_patterns = [
                'system(', 'exec(', 'popen(', 'fork()', 'unlink(', 'remove(',
                'rm -rf', 'chmod(', 'chown('
            ]
            for pattern in dangerous_patterns:
                if pattern in code:
                    self.logger.warning(f"Safety check detected potentially unsafe C code: {pattern}")
                    if self.safety_enabled:
                        return f"[Safety Warning] Potentially unsafe C code detected: '{pattern}'. Execution aborted."

        if safety and input("Execute code? y/n ") != "y":
            return "Code rejected by user."

        exec_extension = ".exe" if os.name == "nt" else ""  # Windows uses .exe, Linux/Unix does not

        with tempfile.TemporaryDirectory() as tmpdirname:
            source_file = os.path.join(tmpdirname, "temp.c")
            exec_file = os.path.join(tmpdirname, "temp") + exec_extension
            with open(source_file, 'w') as f:
                f.write(code)

            try:
                compile_command = ["gcc", source_file, "-o", exec_file]
                compile_result = subprocess.run(
                    compile_command,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if compile_result.returncode != 0:
                    self.logger.error(f"Compilation failed: {compile_result.stderr}")
                    return f"Compilation failed: {compile_result.stderr}"

                run_command = [exec_file]
                run_result = subprocess.run(
                    run_command,
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if run_result.returncode != 0:
                    self.logger.error(f"Execution failed: {run_result.stderr}")
                    return f"Execution failed: {run_result.stderr}"
                output = run_result.stdout
                self.logger.info(f"C code executed successfully")

            except subprocess.TimeoutExpired as e:
                self.logger.error(f"Execution timed out: {str(e)}")
                return f"Execution timed out: {str(e)}"
            except FileNotFoundError:
                self.logger.error("'gcc' not found")
                return "Error: 'gcc' not found. Ensure a C compiler (e.g., gcc) is installed and in PATH."
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
            r"segmentation fault", 
            r"core dumped", 
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
#include <stdio.h>
#include <stdlib.h>

void hello() {
    printf("Hello, World!\\n");
}
""",
"""
int main() {
    hello();
    return 0;
}
    """]
    c = CInterpreter()
    print(c.execute(codes))