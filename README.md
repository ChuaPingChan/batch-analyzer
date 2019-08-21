## Introduction
This is a basic Batch analyzer

Features:
1. Trace batch runtime execution

## Usage
Trace batch runtime execution
1. Add a JSON configuration file, refer to "sample.json"
1. Inject echo statements in batch subroutines entry points by running

    ```
    python Parser.py --config="<config_JSON>" --injectEchos
    ```
1. Run batch scripts
1. "logs/trace.log" or your configured log file will be generated
