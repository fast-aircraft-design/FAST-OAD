"""
Enables to remove duplicate variables from text file
"""

from os import remove


def remove_duplicate(input_file_name: str):
    """
    Removes duplicate lines in a text file

    """
    input_file = open(input_file_name, "r")

    # Store all the variables
    stored_lines = []
    for line in input_file:
        if line not in stored_lines:
            stored_lines.append(line)
    # Delete the file
    input_file.close()
    remove(input_file_name)

    # Create new file
    input_file = open(input_file_name, "w")

    # Write non duplicate lines
    for line in stored_lines:
        input_file.write(str(line))

    input_file.close()


if __name__ == "__main__":
    remove_duplicate("legacy1.txt")
