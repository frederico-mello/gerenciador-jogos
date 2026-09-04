## 1. Inspect route functions

- [x] 1.1 Read each of the 11 affected route functions to determine actual method usage (GET-only, GET+POST, or POST-only)

## 2. Add methods to route decorators

- [x] 2.1 Add `methods=["GET"]` or `methods=["GET", "POST"]` to route at line 90
- [x] 2.2 Add methods to route at line 145
- [x] 2.3 Add methods to route at line 203
- [x] 2.4 Add methods to route at line 295
- [x] 2.5 Add methods to route at line 386
- [x] 2.6 Add methods to route at line 537
- [x] 2.7 Add methods to route at line 583
- [x] 2.8 Add methods to route at line 673
- [x] 2.9 Add methods to route at line 727
- [x] 2.10 Add methods to route at line 854
- [x] 2.11 Add methods to route at line 930

## 3. Verification

- [x] 3.1 Run `python -m pytest` to verify no regressions
- [x] 3.2 Spot-check 2-3 routes in dev server to confirm GET/POST behavior unchanged
