def say_hello():
    """Simple function to print a greeting."""
    print("Hello, World! Your Python environment is working correctly.")

    # Print Python version
    import sys
    print(f"Python version: {sys.version}")

    # Print location of Python interpreter
    print(f"Python interpreter path: {sys.executable}")


if __name__ == "__main__":
    say_hello()