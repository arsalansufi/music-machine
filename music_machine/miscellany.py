"""
A module containing miscellaneous functions.
"""


def log(message, length=80, padding='-'):
    """
    A function to format and print messages. Pads the provided message with additional characters
    to bring it to the specified length.
    """
    print message + ' ' + (length - len(message) - 1) * padding
