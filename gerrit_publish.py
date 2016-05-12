from shpy import *

parser.add_argument("to", type=str)

def verify_inside_repo():
    root = c("git rev-parse --show-toplevel", exit=True)
    if len(root) == 0:
        p("Not inside repo")
        sys.exit(1)

def verify_staged_changes():
    cached = c("git diff --cached --name-only")
    if len(cached) > 0:
        p("Warning: You have staged changes")

def main(prompt_answers=[]):
    a = init()
    verify_inside_repo()
    verify_staged_changes()
    upstream = "HEAD^"
    starting_commit = c("git rev-parse HEAD")[0]
    try:
        c("git reset --soft {}", upstream)
        c("git commit -m 'test publish'")
        squash_commit = c("git rev-parse HEAD")[0]
        c("git reset --soft {}", starting_commit)
        c("git update-ref MERGE_HEAD {}", squash_commit)
        c("git commit -m 'back-merge'")
    except Exception:
        c("git reset --soft {}", starting_commit)
        raise

def prompt_user(options, prompt_answers):
    if len(prompt_answers) > 0:
        assert prompt_answers[0] in options, "Bad prompt answer"
        return prompt_answers.pop()

if __name__ == '__main__':
    main()
