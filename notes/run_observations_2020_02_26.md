## 02-26-2020 Run Observations

`Present: Kev + Henry`

### Notes

* continues to try to enter the same locked door
* presses the facebook button in the contacts menu (needs to be able to press back / reset when stuck)
* pressing red x from clothes thing just fine
* needs to be better at following bus routes — it presses the button but then nothing happens so it presses something else really quickly.
* phone stream turns gray and crashes: `error in python3: double free or corruption (fasttop)`. This should hopefully resolve itself with move to web visuals.
* ai or maybe device server out of memory error, GC overhead limit exceeded.

### Takeaways

* have two first things to work on
* 1) connect web visuals to existing system to remove opencv drawing crashes
* 2) wrap all processes in strong terminal app that collects logs, is interactive, and restarts any process on crash
