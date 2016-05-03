from cStringIO import StringIO
from gerrit_publish import *
import argparse
import os
import shlex
import subprocess
import sys
import tempfile
import unittest

rootlogger = logging.getLogger()
rootlogger.setLevel(logging.DEBUG)


class TestPublish(unittest.TestCase):
    def setUp(self):
        self.oldargv = sys.argv
        self.oldcwd = os.getcwd()

    def tearDown(self):
        sys.argv = self.oldargv
        os.chdir(self.oldcwd)

    def test_simple_publish(self):
        self.given_test_repo()
        self.make_commit()
        my_commit = self.run_command("git rev-parse HEAD")[0]
        out = self.run_publish("origin/master")
        first_parent = self.run_command("git rev-parse HEAD^")[0]
        back_merge = self.run_command("git rev-parse HEAD")[0]
        second_parent = self.run_command("git rev-parse HEAD^2")[0]
        self.assertNotEqual(my_commit, back_merge)
        self.assertNotEqual(first_parent, second_parent)
        self.assertEqual(my_commit, first_parent)

    def test_no_upstream_given(self):
        self.given_test_repo()
        out = self.run_publish("", True)
        self.assertTrue(out.startswith("usage: "), out)

    def test_not_in_repo(self):
        os.chdir("/tmp")
        out = self.run_publish("lsv", True)
        self.assertIn("Not inside repo", out, "No warning about outside repo:\n{}".format(out))

    def test_help_argument(self):
        out = self.run_publish("--help", True)
        self.assertTrue(out.startswith('usage:'), "Wrong output from --help:\n{}".format(out))
        self.assertNotIn("error: ", out, "Error in --help:\n{}".format(out))

    def make_commit(self):
        self.run_command("git commit --allow-empty -m test")

    def given_test_repo(self):
        test_data = "{}/test_data".format(os.getcwd())
        if not os.path.exists(test_data):
            os.makedirs(test_data)
        repo_dir = tempfile.mkdtemp(dir=test_data)
        os.chdir(repo_dir)
        self.run_command("git init")
        self.run_command("git config user.name 'gerrit publish'")
        self.run_command("git config user.email 'gerrit@publish.com'")
        self.run_command("git commit --allow-empty -m 'Initial commit'")
        self.assertEqual(repo_dir, self.run_command("git rev-parse --show-toplevel"))
        return repo_dir

    def run_publish(self, args, should_crash=False):
        oldstdout = sys.stdout
        oldstderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = sys.stdout


        sys.stdout.seek(0)
        splitted = shlex.split(args)
        sys.argv = ["gerrit_publish"] + splitted
        if should_crash:
            with self.assertRaises(SystemExit):
                main()
        else:
            main()

        ret = sys.stdout.getvalue().strip()
        sys.stdout = oldstdout
        sys.stderr = oldstderr

        return ret

    def run_command(self, command):
        with open(os.devnull, 'w') as shutup:
            return subprocess.check_output(shlex.split(command)).strip()

if __name__ == '__main__':
    unittest.main(verbosity=2)
