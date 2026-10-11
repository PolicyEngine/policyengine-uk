#! /usr/bin/env bash
# Tag the commit a release was built from: .github/publish-git-tag.sh VERSION SHA [MESSAGE_FILE]
#
# Creates the annotated tag VERSION at SHA, the version commit the release
# workflow built, tested and published, and pushes it. If the tag already
# exists on origin at SHA (a re-run), it does nothing. If it exists at another
# commit, or anything fails, it exits non-zero: it never moves or deletes a
# tag, and never ignores a failed push.
#
# Before this, the script tagged whatever HEAD was and ran `git push --tags
# || true`, so a tag could land on a later commit than the release, and a
# failed push went unnoticed.
set -euo pipefail

if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
  echo "usage: $0 VERSION SHA [MESSAGE_FILE]" >&2
  exit 2
fi
version=$1
sha=$2
message_file=${3:-}

if ! [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "error: version '$version' is not X.Y.Z" >&2
  exit 2
fi
if ! [[ "$sha" =~ ^[0-9a-f]{40}$ ]] || ! git cat-file -e "$sha^{commit}" 2>/dev/null; then
  echo "error: '$sha' is not a full SHA of a commit in this repository" >&2
  exit 2
fi

git_bot() {
  git -c user.name="github-actions[bot]" \
    -c user.email="41898282+github-actions[bot]@users.noreply.github.com" "$@"
}

# The commit the remote tag points at, peeled through an annotated tag.
remote_target() {
  local refs peeled direct
  refs=$(git ls-remote --tags origin "refs/tags/$version" "refs/tags/$version^{}")
  peeled=$(awk -v ref="refs/tags/$version^{}" '$2 == ref { print $1 }' <<<"$refs")
  direct=$(awk -v ref="refs/tags/$version" '$2 == ref { print $1 }' <<<"$refs")
  echo "${peeled:-$direct}"
}

existing=$(remote_target)
if [ -n "$existing" ]; then
  if [ "$existing" = "$sha" ]; then
    echo "Tag $version already points at $sha; nothing to do."
    exit 0
  fi
  echo "error: tag $version already exists at $existing, not $sha; leaving it alone" >&2
  exit 1
fi

if git rev-parse -q --verify "refs/tags/$version" >/dev/null; then
  local_target=$(git rev-parse "refs/tags/$version^{commit}")
  if [ "$local_target" != "$sha" ]; then
    echo "error: a local tag $version points at $local_target, not $sha" >&2
    exit 1
  fi
else
  if [ -n "$message_file" ]; then
    git_bot tag --annotate --file "$message_file" "$version" "$sha"
  else
    git_bot tag --annotate --message "policyengine-uk $version" "$version" "$sha"
  fi
fi

git push origin "refs/tags/$version"

pushed=$(remote_target)
if [ "$pushed" != "$sha" ]; then
  echo "error: after the push, origin's tag $version points at '${pushed}', not $sha" >&2
  exit 1
fi
echo "Tagged $sha as $version."
