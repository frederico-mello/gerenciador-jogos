## 1. Fix scripts/run-as-app.sh

- [x] 1.1 Replace `[ condition ]` with `[[ condition ]]` at line 15

## 2. Fix deploy/setup.sh

- [x] 2.1 Replace `[ condition ]` with `[[ condition ]]` at line 12
- [x] 2.2 Replace at line 34
- [x] 2.3 Replace at line 44
- [x] 2.4 Replace at line 46
- [x] 2.5 Replace at line 64
- [x] 2.6 Replace at line 86
- [x] 2.7 Replace at line 100
- [x] 2.8 Replace at line 116
- [x] 2.9 Replace at line 136

## 3. Verification

- [x] 3.1 Run `bash -n deploy/setup.sh` to verify syntax
- [x] 3.2 Run `bash -n scripts/run-as-app.sh` to verify syntax
