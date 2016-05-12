from cStringIO import StringIO
from gerrit_publish import *
import argparse
import os
import shlex
import subprocess
import sys
import tempfile
import unittest

## TODO:
## Publish with unstaged

class TestPublish(unittest.TestCase):
    def setUp(self):
        self.debug = True
        self.oldargv = sys.argv
        self.oldcwd = os.getcwd()
        self.prompt_answers = []

    def tearDown(self):
        sys.argv = self.oldargv
        os.chdir(self.oldcwd)
        self.assertEqual([], self.prompt_answers)

    def test_rollback_if_error(self):
        self.given_test_repo()
        old_head = self.rev_parse("HEAD")
        old_status = self.run_command("git status")
        self.run_publish("origin/master", should_crash=True)
        new_head = self.rev_parse("HEAD")
        new_status = self.run_command("git status")
        self.assertEqual(old_head, new_head)
        self.assertEqual(old_status, new_status)

    def test_publish_with_staged_changes(self):
        self.given_test_repo()
        self.write_file("test_file", "Hello world")
        self.run_command("git add test_file")
        out = self.run_publish("origin/master")
        self.assertTrue("Warning:" in out)

    def test_publish_with_unstaged_changes(self):
        self.given_test_repo()
        self.write_file("test_file", "Hello world")
        self.run_command("git add test_file")
        self.prepare_commit("My commit msg")
        self.run_command("git commit")
        with open("test_file", "w") as text_file:
            text_file.write("goodbye world")
        self.run_publish("origin/master")

    def test_prompt_user(self):
        self.prompt_answers.insert(0,"n")
        self.assertEqual("n", prompt_user(["y", "n"], self.prompt_answers))

    def test_commit_without_editor(self):
        self.given_test_repo()
        self.prepare_commit("My commit msg")
        self.run_command("git commit --allow-empty")
        self.assertEqual("My commit msg", self.commit_msg("HEAD"))

    def test_simple_publish(self):
        self.given_test_repo()
        self.make_commit("test_file", "Hello world", "Test commit")
        my_commit = self.rev_parse("HEAD")
        out = self.run_publish("origin/master")
        first_parent = self.rev_parse("HEAD^")
        back_merge = self.rev_parse("HEAD")
        second_parent = self.rev_parse("HEAD^2")
        self.assertNotEqual(my_commit, back_merge)
        self.assertNotEqual(first_parent, second_parent)
        self.assertEqual(my_commit, first_parent)

    def test_no_upstream_given(self):
        self.given_test_repo()
        out = self.run_publish("", True)
        self.assertTrue(out.startswith("usage: "), out)

    def test_not_in_repo(self):
        os.chdir("/")
        out = self.run_publish("lsv", True)
        self.assertIn("Not inside repo", out, "No warning about outside repo:\n{}".format(out))

    def test_help_argument(self):
        out = self.run_publish("--help", True)
        self.assertTrue(out.startswith('usage:'), "Wrong output from --help:\n{}".format(out))
        self.assertNotIn("error: ", out, "Error in --help:\n{}".format(out))

    def prepare_commit(self, message):
        os.environ["EDITOR"] = "mv .git/COMMIT_EDITMSG2 "
        with open(".git/COMMIT_EDITMSG2", "w") as text_file:
                text_file.write(message)

    def given_test_repo(self):
        test_data = "{}/test_data".format(os.getcwd())
        if not os.path.exists(test_data):
            os.makedirs(test_data)
        repo_dir = tempfile.mkdtemp(prefix=self.id().split('.')[-1] + "_", dir=test_data)
        print(repo_dir)
        os.chdir(repo_dir)
        self.run_command("git init")
        self.run_command("git config user.name 'gerrit publish'")
        self.run_command("git config user.email 'gerrit@publish.com'")
        self.run_command("git commit --allow-empty -m 'Initial commit'")
        self.run_command("git commit --allow-empty -m 'Second commit'")
        toplevel = self.rev_parse("--show-toplevel")
        self.assertEqual(repo_dir, toplevel)
        return repo_dir

    def run_publish(self, args, should_crash=False):
        oldstdout = sys.stdout
        oldstderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = sys.stdout

        splitted = shlex.split(args)
        if self.debug:
            splitted = ["-vvv"] + splitted

        sys.argv = ["gerrit_publish"] + splitted
        if should_crash:
            with self.assertRaises(BaseException):
                main(prompt_answers=self.prompt_answers)
        else:
            main(prompt_answers=self.prompt_answers)

        ret = sys.stdout.getvalue().strip()
        sys.stdout = oldstdout
        sys.stderr = oldstderr

        if self.debug:
            print ret

        return ret

    def write_file(self, filename, content):
        with open(filename, "w") as text_file:
            text_file.write(content)

    def make_commit(self, filename, content, message):
        self.write_file(filename, content)
        self.run_command("git add {}".format(filename))
        self.prepare_commit(message)
        self.run_command("git commit")

    def run_command(self, command):
        return subprocess.check_output(shlex.split(command)).splitlines()

    def commit_msg(self, commit):
        return "\n".join(self.run_command("git log --format=%B -n 1 {}".format(commit))).strip()

    def rev_parse(self, rev):
        return self.run_command("git rev-parse {}".format(rev))[0]

if __name__ == '__main__':
    unittest.main(verbosity=0)
