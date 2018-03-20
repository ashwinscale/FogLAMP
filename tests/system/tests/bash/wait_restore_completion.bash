#!/bin/bash

$TEST_BASEDIR/bash/wait_foglamp_status.bash "STOPPED"
$TEST_BASEDIR/bash/wait_foglamp_status.bash "RUNNING"
