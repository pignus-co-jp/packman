# -*- coding: utf-8 -*-

from pydantic import BaseModel, Field
from typing import Optional


class RemoteEntry(BaseModel):
    name: str
    path: str
    is_dir: bool
