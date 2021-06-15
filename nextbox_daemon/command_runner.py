import select
import subprocess
import logging
import queue
import time
import shlex


from nextbox_daemon.config import log


class CommandRunner:
    def __init__(self, cmd, cb_parse=None, block=False, start=True, shell=False):
        self.block = block
        self.cb = cb_parse

        self._parsed = {}
        if isinstance(cmd, str):
            cmd = shlex.split(cmd)
        self.cmd = cmd
        self.q_output = queue.Queue()
        self._output = []
        self.returncode = None
        self.proc = None
        self.started = False
        self.user_info = None
        self.shell = shell

        if start:
            self.start()


    @classmethod
    def retries(cls, count, *vargs, **kwargs):
        # cannot retry, if non-blocking
        if kwargs.get("block"):
            log.warning("trying CommandRunner-retries w/o block: no retries are done!")
            return cls(*vargs, **kwargs)

        # if 'block' is set, retry until returncode == 0
        for idx in range(count):
            res = cls(*vargs, **kwargs)
            if res.returncode == 0:
                return res
            log.debug(f"retry #{idx+1}, returncode: {res.returncode}")

        # failed retries
        log.error("retried hard for {count} times, failed anyways")
        res.log_output()
        return res


    def start(self):
        if self.started:
            log.warning(f"trying to start already started: {self.cmd}")
            return False

        self.cmd = self.cmd if not self.shell else " ".join(self.cmd)
        self.proc = subprocess.Popen(self.cmd, shell=self.shell,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        self.started = time.time()
        log.debug(f"started {self.cmd} ({'non-' if not self.block else ''}blocking)")

        # return if non-blocking, else wait + pass-on output
        if not self.block:
            return True

        log.debug("blocking call, waiting now...")

        while self.proc.returncode is None:
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                log.debug("blocking-cmd timeout (10secs)")

        self._handle_stdout_stream(poll_block_ms=1000)
        log.debug("blocking call finished")
        return True

    def _handle_stdout_stream(self, poll_block_ms=1):
        if not self.proc:
            return None

        if self.returncode is not None:
            return None

        sel = select.poll()
        sel.register(self.proc.stdout, select.POLLIN)
        line = None
        empty_line = False
        while line != b"":
            # max wait in milliseconds for new inputs
            if not sel.poll(poll_block_ms):
                break

            raw_line = self.proc.stdout.readline().decode("utf-8")
            line = raw_line.strip().split(r"\b")[-1].strip()
            toks = line.split()
            self.q_output.put(line)

            # empty line (we skip the 1st, but a 2nd leads to a break)
            if len(toks) == 0:
                if not empty_line:
                    empty_line = True
                    continue
                break

        if self.proc.poll() is not None:
            self.returncode = self.proc.returncode

    def get_new_output(self):
        self._handle_stdout_stream()

        if self.q_output.qsize() == 0:
            return None

        out = []
        try:
            while True:
                line = self.q_output.get_nowait()
                out.append(line)
                # parse line, if callback `cb` was provided
                if self.cb:
                    self.cb(line, self._parsed)
        except queue.Empty:
            pass

        self._output.extend(out)
        return out

    def tail(self, num_lines=10):
        return self.output[-num_lines:]

    def info(self):
        return f"cmd: {self.cmd}, returncode: {self.returncode}"

    def log_output(self):
        log.info(f"#### log output for command: {self.cmd}")
        for line in self.output:
            log.info(line)
        log.info(f"#### log output end")

    @property
    def output(self):
        self.get_new_output()
        return self._output[:]

    @property
    def parsed(self):
        if not self.cb:
            return {}

        self.get_new_output()
        return dict(self._parsed)

    @property
    def running(self):
        if self.returncode is not None or self.proc is None:
            return False

        if self.proc and self.proc.poll() is not None:
            self.returncode = self.proc.returncode
            return False
        return True

    @property
    def finished(self):
        if self.returncode is not None:
            return True

        if self.proc and self.proc.poll() is not None:
            self.returncode = self.proc.returncode
            return True
        return False

