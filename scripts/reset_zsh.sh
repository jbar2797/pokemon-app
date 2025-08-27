#!/usr/bin/env zsh
# Reset aggressive zsh options that may have been set by pasted Bash blocks.
setopt LOCAL_OPTIONS
unsetopt nounset 2>/dev/null
unsetopt errexit 2>/dev/null
unsetopt pipefail 2>/dev/null
print "zsh options reset (nounset/errexit/pipefail disabled for this session)."
