"""Base-versus-head aggregate impact report on a certified dataset.

The report measures one model checkout at a time (``measure``), on a dataset
whose bytes are verified against a pinned SHA-256, and then compares two
measurements (``compare``). A pull request's CI measures its base and its head
on the same dataset and posts the comparison as a comment.

This package must only import ``policyengine_uk`` through its public
simulation API, and must import its own modules relatively: CI runs the pull
request head's copy of it against the base checkout's model.
"""

TOOL_SCHEMA = "policyengine-uk-aggregate-impact/1"
COMMENT_MARKER = "<!-- policyengine-uk-aggregate-impact -->"
