"""File models."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any


class FileNode(BaseModel):
    """File or directory node."""
    name: str
    path: str
    absolute: str
    type: Literal["file", "directory"]
    ignored: bool


class FileHunk(BaseModel):
    """Git patch hunk."""
    old_start: int = Field(..., alias="oldStart")
    old_lines: int = Field(..., alias="oldLines")
    new_start: int = Field(..., alias="newStart")
    new_lines: int = Field(..., alias="newLines")
    lines: List[str]
    
    class Config:
        populate_by_name = True


class FilePatch(BaseModel):
    """Git patch."""
    old_file_name: str = Field(..., alias="oldFileName")
    new_file_name: str = Field(..., alias="newFileName")
    old_header: Optional[str] = Field(None, alias="oldHeader")
    new_header: Optional[str] = Field(None, alias="newHeader")
    hunks: List[FileHunk]
    index: Optional[str] = None
    
    class Config:
        populate_by_name = True


class FileContent(BaseModel):
    """File content."""
    type: Literal["text", "binary"]
    content: str
    diff: Optional[str] = None
    patch: Optional[FilePatch] = None
    encoding: Optional[Literal["base64"]] = None
    mime_type: Optional[str] = Field(None, alias="mimeType")
    
    class Config:
        populate_by_name = True


class FileStatus(BaseModel):
    """Git file status."""
    path: str
    added: int
    removed: int
    status: Literal["added", "deleted", "modified"]


class Range(BaseModel):
    """Text range."""
    start_line: int = Field(..., alias="startLine")
    start_character: int = Field(..., alias="startCharacter")
    end_line: int = Field(..., alias="endLine")
    end_character: int = Field(..., alias="endCharacter")
    
    class Config:
        populate_by_name = True


class Symbol(BaseModel):
    """Workspace symbol."""
    name: str
    kind: int
    location: Dict[str, Any]


class TextSearchMatch(BaseModel):
    """Text search match."""
    path: Dict[str, str]
    lines: Dict[str, str]
    line_number: int = Field(..., alias="lineNumber")
    absolute_offset: int = Field(..., alias="absoluteOffset")
    submatches: List[Dict[str, Any]] = []
    
    class Config:
        populate_by_name = True
    
    @property
    def path_text(self) -> str:
        """Get path as string."""
        return self.path.get("text", "") if isinstance(self.path, dict) else str(self.path)
    
    @property
    def lines_text(self) -> str:
        """Get lines as string."""
        return self.lines.get("text", "") if isinstance(self.lines, dict) else str(self.lines)


class FindFilesParams(BaseModel):
    """Parameters for finding files."""
    query: str
    type: Optional[Literal["file", "directory"]] = None
    directory: Optional[str] = None
    limit: Optional[int] = None
    dirs: Optional[str] = None