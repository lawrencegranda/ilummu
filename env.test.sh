#!/bin/bash
#-------------------------------------------------------------------------------
# Edify
# env.sh: Environment variables for dev 
#
# Duplicate this file, rename it "env.sh", edit it and run it to initialize
# necessary environment variables. If you are missing the variable names
# contact Lawrence Granda
#
# The values present here are defaults and should never be used on production.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Environment Settings
#-------------------------------------------------------------------------------
export ENV='TEST'
export MAINTENANCE_MODE=0


#-------------------------------------------------------------------------------
# Flask
#-------------------------------------------------------------------------------
export SECRET_KEY='test_key'


#-------------------------------------------------------------------------------
# SQLALCHEMY
#-------------------------------------------------------------------------------
export DB_URL=''