# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2021 Taneli Hukkinen
# Licensed to PSF under a Contributor Agreement.

# Wildcard imports that pollute the namespace.
# Real-world messy package initializer.
from ._parser import *
from ._re import *
from ._types import *

# Pretend this exception was created here.
TOMLDecodeError.__module__ = __name__
