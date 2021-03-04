const childProcess = require('child_process')
const moment = require('moment')
const treeKill = require('tree-kill')
const { logToDashboard, genlog, getProcessLogger } = require('./dashboard')
const { delay } = require('./util')

class KimProcess {
  constructor(ops) {
    const { name, abbrev, script, index, onLog, onStart, onExit } = ops
    this.ops = ops
    this.name = name
    this.abbrev = abbrev
    this.script = script
    this.index = index
    this.onLog = onLog
    this.onStart = onStart
    this.onExit = onExit

    const colors = ['blue', 'yellow', 'magenta', 'cyan', 'white', 'red']
    const logColors = ['#8282ff', 'yellow', 'magenta', 'cyan', '#ff8a00', '#ff8aff']
    this.color = colors[index] || colors[0]
    this.logColor = logColors[index] || logColors[0]

    const isAI = abbrev === 'AI'
    this.logger = getProcessLogger({ name, index, isMain: isAI, color: this.logColor })

    this.started = false
    this.running = false
    this.cancelled = false
    this.logs = []
    this.errs = []
    this.stopTimes = []

    this.logLimit = 1000
    this.errLimit = 1000
    this.timeBetweenScriptRuns = 3000
  }

  logChildStreamBuferData(type, buffer) {
    const isErr = type === 'stderr'

    const lines = buffer.toString('utf8').trimRight().split('\n')

    const logLines = isErr ? lines.map(l => l.red) : lines
    logToDashboard(this.logger, ...logLines)

    if (this.onLog) {
      this.onLog(logLines)
    }

    const arr = isErr ? this.errs : this.logs
    const limit = isErr ? this.errLimit : this.logLimit
    logLines.forEach(line => {
      arr.unshift({ when: moment(), line })
    })

    if (arr.length > limit) {
      arr.splice(limit, arr.length - limit)
    }

    this.lastLogTime = Date.now()
  }

  getLabel = () => this.child ? `${this.name} (PID ${this.child.pid})` : this.name

  runScript() {
    return new Promise((resolve, reject) => {
      if (this.child) {
        this.killChild()
      }

      this.running = true
      const child = this.child = childProcess.spawn(this.script, {
        env: {
          ...process.env,
          PROCESS_HUB: 'true'
        }
      })

      genlog(`Started Process - ${this.getLabel()}`.green)

      const listenToStream = (name) => {
        child[name].setEncoding('utf8')
        child[name].on('data', data => this.logChildStreamBuferData(name, data))
      }

      listenToStream('stdout')
      listenToStream('stderr')

      this.lastLogTime = Date.now()
      const monitorInterval = setInterval(() => {
        if (!this.running) {
          return
        }

        const { maxTimeBetweenLogs } = this.ops
        if (maxTimeBetweenLogs && Date.now() - this.lastLogTime > maxTimeBetweenLogs) {
          if (monitorInterval) {
            clearInterval(monitorInterval)
            genlog(`Killing Inactive Process - ${this.getLabel()}`.red)
            this.killChild()
          }
        }
      }, 1000)

      // child.on('error', err => {
      //   console.log(err)
      // })

      child.on('exit', exitCode => {
        this.running = false

        if (!exitCode) {
          resolve()
        } else {
          reject(`${this.name} Error: exited with code: ${exitCode}`)
        }
      })
    })
  }

  async startLoop() {
    if (this.started && !this.cancelled) {
      return
    }

    this.started = true
    this.cancelled = false

    while (!this.cancelled) {
      if (this.onStart) {
        this.onStart({ kimProcess: this })
      }

      await this.runScript()
        .then(() => {
          this.stopTimes.push({ err: null, when: moment() })
          genlog(`Clean exit - ${this.getLabel()}`.yellow)
        })
        .catch(err => {
          this.stopTimes.push({ err, when: moment() })
          genlog(`${this.getLabel()} - Crash #${this.stopTimes.length} Error:`.red, err)
        })

      if (this.onExit) {
        this.onExit({ kimProcess: this, cancelled: this.cancelled, err: this.stopTimes[this.stopTimes.length - 1].err })
      }

      await delay(this.timeBetweenScriptRuns)
    }
  }

  killChild(sig = 'SIGTERM') {
    return new Promise((resolve, reject) => {
      if (!this.child) {
        return resolve()
      }

      treeKill(this.child.pid, sig, err => {
        return err ? reject(err) : resolve()
      })
    })
  }

  cancelProcess() {
    this.cancelled = true
    return this.killChild()
  }
}

module.exports = { KimProcess }
