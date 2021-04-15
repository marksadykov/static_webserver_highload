#!/usr/bin/env pypy
import sys
import struct, re, linecache

# ____________________________________________________________

STM_TRANSACTION_START   = 0
STM_TRANSACTION_COMMIT  = 1
STM_TRANSACTION_ABORT   = 2

# contention; see details at the start of contention.c
STM_CONTENTION_WRITE_WRITE = 3   # markers: self loc / other written loc
STM_CONTENTION_WRITE_READ  = 4   # markers: self written loc / other missing
STM_CONTENTION_INEVITABLE  = 5   # markers: self loc / other inev loc

# following a contention, we get from the same thread one of
# STM_ABORTING_OTHER_CONTENTION, STM_TRANSACTION_ABORT (self-abort),
# or STM_WAIT_CONTENTION (self-wait).
STM_ABORTING_OTHER_CONTENTION = 6

# always one STM_WAIT_xxx followed later by STM_WAIT_DONE
STM_WAIT_FREE_SEGMENT  = 7
STM_WAIT_SYNC_PAUSE    = 8
STM_WAIT_CONTENTION    = 9
STM_WAIT_DONE          = 10

# start and end of GC cycles
STM_GC_MINOR_START  = 11
STM_GC_MINOR_DONE   = 12
STM_GC_MAJOR_START  = 13
STM_GC_MAJOR_DONE   = 14

_STM_EVENT_N  = 15

PAUSE_AFTER_ABORT   = 0.000001      # usleep(1) after every abort


event_name = {}
for _key, _value in globals().items():
    if _key.startswith('STM_'):
        event_name[_value] = _key

# ____________________________________________________________


class LogEntry(object):
    def __init__(self, timestamp, threadnum, otherthreadnum,
                 event, marker1, marker2, frac):
        self.timestamp = timestamp
        self.threadnum = threadnum
        self.otherthreadnum = otherthreadnum
        self.event = event
        self.marker1 = marker1
        self.marker2 = marker2
        self.frac = frac

    def __str__(self):
        s = '[%.3f][%s->%s]\t%s' % (
            self.timestamp, self.threadnum, self.otherthreadnum,
            event_name[self.event])
        if self.marker1:
            s += ':\n%s' % print_marker(self.marker1)
        if self.marker2:
            s += '\n%s' % print_marker(self.marker2)
        return s


def parse_log(filename):
    f = open(filename, 'rb')
    try:
        header = f.read(16)
        if header != "STMGC-C7-PROF01\n":
            raise ValueError("wrong format in file %r" % (filename,))
        f.seek(0, 2)
        frac = 1.0 / f.tell()
        f.seek(16, 0)
        result = []
        while True:
            packet = f.read(19)
            if len(packet) < 19: break
            sec, nsec, threadnum, otherthreadnum, event, len1, len2 = \
                  struct.unpack("IIIIBBB", packet)
            if event >= _STM_EVENT_N:
                raise ValueError("the file %r appears corrupted" % (filename,))
            m1 = f.read(len1)
            m2 = f.read(len2)
            yield LogEntry(sec + 0.000000001 * nsec,
                           threadnum, otherthreadnum, event, m1, m2,
                           f.tell() * frac)
    finally:
        f.close()


class ThreadState(object):
    def __init__(self, threadnum):
        self.threadnum = threadnum
        self.cpu_time = 0.0

    def transaction_start(self, entry):
        self._start = entry
        self._conflict = None
        self._pause = None
        self._paused_time = 0.0

    def transaction_stop(self, entry):
        transaction_time = entry.timestamp - self._start.timestamp
        transaction_time -= self._paused_time
        assert transaction_time >= 0.0
        self.cpu_time += transaction_time
        self._start = None
        self._pause = None
        if self._conflict and entry.event == STM_TRANSACTION_ABORT:
            c = self._conflict[1]
            c.aborted_time += transaction_time
            c.paused_time += PAUSE_AFTER_ABORT
            self._conflict = None

    def transaction_pause(self, entry):
        self._pause = entry

    def transaction_unpause(self, entry):
        if self._pause is None:
            return
        pause_time = entry.timestamp - self._pause.timestamp
        self._paused_time += pause_time
        self._pause = None
        if self._conflict and self._conflict[0] == "local":
            c = self._conflict[1]
            c.paused_time += pause_time
            self._conflict = None

    def in_transaction(self):
        return self._start is not None


class ConflictSummary(object):
    def __init__(self, event, marker1, marker2):
        self.event = event
        self.marker1 = marker1
        self.marker2 = marker2
        self.aborted_time = 0.0
        self.paused_time = 0.0
        self.num_events = 0
        self.timestamps = []

    def sortkey(self):
        return self.aborted_time + self.paused_time

    def get_event_name(self):
        return event_name[self.event]

    def get_marker1(self):
        return print_marker(self.marker1)

    def get_marker2(self):
        return print_marker(self.marker2)

    def __str__(self):
        s = '%.3fs lost in aborts, %.3fs paused (%dx %s)\n' % (
            self.aborted_time, self.paused_time, self.num_events,
            self.get_event_name())
        s += print_marker(self.marker1)
        if self.marker2:
            s += '\n%s' % print_marker(self.marker2)
        return s




r_marker = re.compile(r'File "(.+)", line (\d+)')

def print_marker(marker):
    s = '  %s' % marker
    match = r_marker.match(marker)
    if match:
        line = linecache.getline(match.group(1), int(match.group(2)))
        line = line.strip()
        if line:
            s += '\n    %s' % line
    return s

def percent(fraction, total):
    r = '%.1f' % (fraction * 100.0 / total)
    if len(r) > 3:
        r = r.split('.')[0]
    return r + '%'

def summarize_log_entries(logentries, stmlog):
    threads = {}
    conflicts = {}
    cnt = 0
    for entry in logentries:
        if (cnt & 0x7ffff) == 0:
            if cnt == 0:
                start_time = entry.timestamp
            else:
                print >> sys.stderr, '%.0f%%' % (entry.frac * 100.0,),
        cnt += 1
        #
        if entry.event == STM_TRANSACTION_START:
            t = threads.get(entry.threadnum)
            if t is None:
                t = threads[entry.threadnum] = ThreadState(entry.threadnum)
            t.transaction_start(entry)
        elif (entry.event == STM_TRANSACTION_COMMIT or
              entry.event == STM_TRANSACTION_ABORT):
            t = threads.get(entry.threadnum)
            if t is not None and t.in_transaction():
                t.transaction_stop(entry)
        elif entry.event in (STM_CONTENTION_WRITE_WRITE,
                             STM_CONTENTION_WRITE_READ,
                             STM_CONTENTION_INEVITABLE):
            summary = (entry.event, entry.marker1, entry.marker2)
            c = conflicts.get(summary)
            if c is None:
                c = conflicts[summary] = ConflictSummary(*summary)
            c.num_events += 1
            c.timestamps.append(entry.timestamp)
            t = threads.get(entry.threadnum)
            if t is not None and t.in_transaction():
                t._conflict = ("local", c, entry)
        elif entry.event == STM_ABORTING_OTHER_CONTENTION:
            t = threads.get(entry.threadnum)
            if t is not None and t._conflict and t._conflict[0] == "local":
                _, c, entry = t._conflict
                t._conflict = None
                t2 = threads.get(entry.otherthreadnum)
                if t2 is not None and t2.in_transaction():
                    t2._conflict = ("remote", c, entry)
        elif entry.event in (STM_WAIT_SYNC_PAUSE, STM_WAIT_CONTENTION,
                             STM_WAIT_FREE_SEGMENT):
            t = threads.get(entry.threadnum)
            if t is not None and t.in_transaction():
                t.transaction_pause(entry)
        elif entry.event == STM_WAIT_DONE:
            t = threads.get(entry.threadnum)
            if t is not None and t.in_transaction():
                t.transaction_unpause(entry)
    #
    if cnt == 0:
        raise Exception("empty file")
    print >> sys.stderr
    stop_time = entry.timestamp
    stmlog.start_time = start_time
    stmlog.total_time = stop_time - start_time
    stmlog.threads = threads
    stmlog.conflicts = conflicts

def dump_summary(stmlog):
    start_time = stmlog.start_time
    total_time = stmlog.total_time
    print
    print 'Total real time:             %.3fs' % (total_time,)
    #
    total_cpu_time = stmlog.get_total_cpu_time()
    print 'Total CPU time in STM mode:  %.3fs (%s)' % (
        total_cpu_time, percent(total_cpu_time, total_time))
    print
    #
    values = stmlog.get_conflicts()
    for c in values[:15]:
        intervals = 48
        timeline = [0] * intervals
        for t in c.timestamps:
            idx = int((t - start_time) / total_time * intervals)
            timeline[idx] += 1

        print str(c)
        print "time line:", "".join(['x' if i else '.' for i in timeline])
        print


class StmLog(object):
    def __init__(self, filename):
        summarize_log_entries(parse_log(filename), self)

    def get_total_cpu_time(self):
        return sum([v.cpu_time for v in self.threads.values()])

    def get_conflicts(self):
        values = self.conflicts.values()
        values.sort(key=ConflictSummary.sortkey)
        values.reverse()
        return values

    def get_total_aborts_and_pauses(self):
        total = 0
        for c in self.conflicts.values():
            total += c.num_events
        return total

    def dump(self):
        dump_summary(self)


def main(argv):
    assert len(argv) == 1, "expected a filename argument"
    StmLog(argv[0]).dump()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
