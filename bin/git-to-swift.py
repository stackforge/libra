#!/usr/bin/env python
##############################################################################
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
##############################################################################


##############################################################################
# To use, cd into the libra git repository you intend to upload (anywhere in
# the working tree is fine) and run this script. It takes no arguments.
##############################################################################


import os
import string
import subprocess
import time
import re
import git

# Constants

git_repo_dir_name = "libra"
supernova_environment = "westswiftt"
swift_container = "git_repo_%s" % git_repo_dir_name
untracked_file_name = "/tmp/untracked_files_in_%s" % git_repo_dir_name
swift_stat_check_timeout = 120

# Ensure the necessary executables are installed.

def assert_executable_exists( name ):
    ret_val = subprocess.call([ "which", "-s", name ])
    if ret_val != 0:
        print "Cannot find executable for %s, please install it; exiting" % name
    assert ret_val == 0

assert_executable_exists( "tar" )
assert_executable_exists( "git" )
assert_executable_exists( "supernova" )
assert_executable_exists( "swift" )

# Create the git repo object and extract info about the current git commit
# from it. That info will be used to build the tarball's (and thus the
# swift object's) name.

repo = git.Repo(".")

assert repo.bare == False
if repo.is_dirty():
    print "ERROR: Cannot tar a repo that is dirty."
    print "Consider 'git stash', maybe?"
assert repo.is_dirty() == False

working_tree_dir = repo.working_tree_dir

git_version_describe = repo.git.describe()
git_date_ci = repo.git.log( "-1", "--pretty=format:%ci" )
git_date_day = string.split( git_date_ci, " " )[0]

git_tarball_filename = "%s_%s_%s.tar.gz" % ( git_repo_dir_name, git_date_day, git_version_describe )

# cd to the root of the git repo.

os.chdir(working_tree_dir)

# Build the tar command.

tar_command = [ "tar", "zc" ]

# We need a list of files to ignore (with tar -X).  First we use the
# documented untracked_files attribute to get a list of untracked
# files and directories. Next we put .git/ on the list since we never
# want that directory.  Then we use a regex hack with "git status"
# to get a list of ignored files.

untracked_file_list = repo.untracked_files
untracked_file_list.append( '.git' )
git_status_output = subprocess.check_output([
    "git", "status", "--ignored", "--short" ],
    stderr=subprocess.STDOUT )
git_status_lines = string.split( git_status_output, "\n" )
for line in git_status_lines:
    line_match = re.match( "^!! (.+)", line )
    if line_match:
        untracked_file_list.append( line_match.group(1) )

# Write that list to /tmp and tell tar to reference it.
# (TODO: learn how to use os.tmpfile and os.path)

with open( untracked_file_name, "w" ) as untracked:
    for filename in untracked_file_list:
        untracked.write( git_repo_dir_name + "/" + filename + "\n" )
    untracked.close()
tar_command.append( "-X" )
tar_command.append( untracked_file_name )

tar_command.append( "-f" )
tar_command.append( git_tarball_filename )
tar_command.append( git_repo_dir_name )

# cd up one directory and write the tarball file.

os.chdir("..")

retval = subprocess.call( tar_command )
assert retval == 0

print "%s/ directory in %s/ tarred:" % ( git_repo_dir_name, os.getcwd() )
retval = subprocess.call([ "ls", "-l", os.getcwd() + "/" + git_tarball_filename ])
assert retval == 0

# Clean up temp file.

os.remove( untracked_file_name )

# Upload the tarball to swift.

retval = subprocess.call([ "supernova", "-x", "swift", supernova_environment,
    "upload", "--skip-identical", swift_container, git_tarball_filename ])
assert retval == 0

print "Tarball uploaded to swift container %s" % swift_container
print "Waiting for swift to acknowledge upload..."

start_time = time.time()
done = False
while not done and time.time() < start_time + swift_stat_check_timeout:
    time.sleep(3)
    # Note: "swift stat" can take 10+ seconds sometimes
    output = subprocess.check_output([ "supernova", "-x", "swift", supernova_environment,
        "stat", swift_container, git_tarball_filename ],
        stderr=subprocess.STDOUT )
    not_found = re.search( '^Object .* not found', output, re.MULTILINE )
    etag_found = re.search( '^ +ETag: ', output, re.MULTILINE )
    # TODO: Checking "Content Length:" to match filesize would be nice too
    done = ( not not_found ) and etag_found

if not done:
    print "ERROR: swift does not acknowledge upload after %s seconds:\n%s" % ( swift_stat_check_timeout, output )
    exit(1)

print output

print "Success!"

