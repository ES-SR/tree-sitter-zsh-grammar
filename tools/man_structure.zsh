#!/usr/bin/env zsh
# man_structure.zsh — surface a man page's structure from its indentation ALONE.
#
# There is no "section"/"subsection" type in the source — only depth of
# indentation. So this assigns each non-blank line a normalized hierarchy level
# derived purely from its leading-whitespace width (distinct widths -> 1,2,3,...
# in ascending order, document order preserved). No regex line-typing.
#
# Input is normalized with `bat --strip-ansi=always --tab=1` (clean text, tabs=1
# space so indent widths are small integers); falls back to a gawk stripper if
# bat is absent. Already-clean text passes through unchanged.
#
# Usage:
#   man_structure.zsh levels  FILE            # <level> <indent> <line>  (all lines)
#   man_structure.zsh outline FILE [MAXLVL]   # only lines at level <= MAXLVL (default 2)
#   man_structure.zsh markers FILE [LEVEL]    # leading-char tally per level (or one level)

emulate -L zsh
setopt extended_glob

cmd=$1 file=$2 arg3=$3
[[ -z $cmd || -z $file ]] && { print -u2 "usage: $0 {levels|outline|markers} FILE [N]"; return 2 }

# --- input normalization ---------------------------------------------------
clean() {
  if (( $+commands[bat] )); then
    bat --color=never --style=plain --strip-ansi=always --tabs=1 -- "$file"
  else
    gawk '{
      gsub(/\x1b\[[0-9;]*[mGKHFJ]/,""); gsub(/.\x08/,""); gsub(/\x0d/,"")
      gsub(/[\x00-\x08\x0B-\x1F\x7F]/,""); print
    }' "$file"
  fi
}

# --- measure indent, then normalize distinct widths into levels ------------
read -r -d '' AwkLevels <<'AWK'
{
  if ($0 ~ /^[[:space:]]*$/) { IND[NR] = -1; LINE[NR] = ""; next }   # blank
  match($0, /^[[:space:]]*/)
  ind = RLENGTH
  IND[NR] = ind
  sub(/^[[:space:]]*/, "")
  LINE[NR] = $0
  Seen[ind] = ind
}
END {
  n = asorti(Seen, Sorted, "@val_num_asc")
  for (i = 1; i <= n; i++) Level[Sorted[i]] = i
  for (r = 1; r <= NR; r++) {
    if (IND[r] == -1) continue                                       # drop blanks
    printf "%d %d %s\n", Level[IND[r]], IND[r], LINE[r]
  }
}
AWK

levels() { clean | gawk "$AwkLevels" }

case $cmd in
  levels)  levels ;;
  outline) levels | awk -v m="${arg3:-2}" '$1 <= m {
             pad=""; for(i=1;i<$1;i++) pad="  "
             txt=$0; sub(/^[0-9]+ [0-9]+ /,"",txt)
             printf "L%d %s%s\n", $1, pad, txt
           }' ;;
  markers) # tally the first character of each line, grouped by level, with an example
    levels | awk -v only="$arg3" '
      { lvl=$1; txt=$0; sub(/^[0-9]+ [0-9]+ /,"",txt)
        c=substr(txt,1,1); key=lvl SUBSEP c
        cnt[key]++; if(!(key in ex)) ex[key]=txt
        lvlseen[lvl]=1 }
      END {
        for (l=1; l<=64; l++) {
          if (!(l in lvlseen)) continue
          if (only != "" && l != only) continue
          printf "=== level %d ===\n", l
          for (k in cnt) { split(k,a,SUBSEP)
            if (a[1]==l) printf "%6d  [%s]  %.70s\n", cnt[k], a[2], ex[k] | "sort -rn" }
          close("sort -rn")
        }
      }' ;;
  *) print -u2 "unknown command: $cmd"; return 2 ;;
esac
