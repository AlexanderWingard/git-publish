from shpy import *

parser.add_argument("to", type=str)

def verify_inside_repo():
    root = c("git rev-parse --show-toplevel", exit=True)
    if len(root) == 0:
        p("Not inside repo")
        sys.exit(1)

def main():
    a = init()
    verify_inside_repo()
    upstream = "HEAD^"
    starting_commit = c("git rev-parse HEAD")[0]
    c("git reset --soft {}", upstream)
    c("git commit --allow-empty -m 'test commit'")
    squash_commit = c("git rev-parse HEAD")[0]
    c("git reset --soft {}", starting_commit)
    c("git update-ref MERGE_HEAD {}", squash_commit)
    c("git commit -m 'back-merge'")

if __name__ == '__main__':
    main()
