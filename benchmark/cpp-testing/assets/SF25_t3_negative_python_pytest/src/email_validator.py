import re
from typing import Optional


class EmailValidator:
    """Validates email addresses according to common rules."""

    PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    def __init__(self, allowed_domains: Optional[list] = None):
        self.allowed_domains = allowed_domains

    def is_valid(self, email: str) -> bool:
        """Check if the email matches the basic pattern."""
        if not self.PATTERN.match(email):
            return False
        if self.allowed_domains:
            domain = email.split('@')[1]
            if domain not in self.allowed_domains:
                return False
        return True

    def normalize(self, email: str) -> str:
        """Normalize email to lowercase and strip whitespace."""
        return email.strip().lower()

    def extract_domain(self, email: str) -> str:
        """Extract the domain part of an email."""
        if '@' not in email:
            raise ValueError(f"Invalid email: {email}")
        return email.split('@')[1].lower()
