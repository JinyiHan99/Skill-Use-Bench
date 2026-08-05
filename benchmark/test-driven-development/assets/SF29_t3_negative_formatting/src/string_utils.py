"""String utility functions.

A collection of helper functions for string manipulation.
This module is fully tested and stable.
"""


def capitalize_words(text:str)->str:
    """Capitalize first letter of each word."""
    return ' '.join(word.capitalize() for word in text.split())


def truncate(text:str, max_length:int, suffix:str='...' )->str:
    """Truncate text to max_length, appending suffix if truncated."""
    if len(text)<=max_length:
        return text
    return text[:max_length-len(suffix)]+suffix


def snake_to_camel( text:str )->str:
    """Convert snake_case to camelCase."""
    parts=text.split('_')
    return parts[0]+  ''.join(p.capitalize() for p in parts[1:])


def camel_to_snake(text:str)->str:
    """Convert camelCase to snake_case."""
    result=[]
    for i,char in enumerate(text):
        if char.isupper() and i>0:
            result.append('_')
        result.append(char.lower())
    return ''.join(result)


def count_vowels(text:str)->int:
    """Count the number of vowels in text."""
    return sum(1 for c in text.lower() if c in 'aeiou')


def reverse_words(text:str)->str:
    """Reverse the order of words in text."""
    return ' '.join(text.split()[::-1])
