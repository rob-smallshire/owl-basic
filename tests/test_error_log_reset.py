"""errors.warning()/error() dedupe by message so a repeated diagnostic is logged
once per compilation. That dedup set is process-global, so it must be reset at the
start of each compilation -- otherwise a warning emitted by one program is silently
swallowed when the next program emits the identical warning. Before the reset every
test that checked a warning had to errors.error_log.clear() by hand.
"""
import logging

from owl_basic.analysis import analyse

# A procedure that ENDPROCs out of an open FOR -- emits the loop-frame leak warning.
_LEAKY = ('PROCf\nEND\n'
          'DEF PROCf\nFOR I% = 1 TO 10\nIF I% = 3 THEN ENDPROC\nNEXT\nENDPROC\n')


def _leak_warnings(caplog):
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        analyse(_LEAKY, name="t")
    return [r.getMessage() for r in caplog.records
            if "reclaimed only by its own" in r.getMessage()]


def test_identical_warning_repeats_across_compilations(caplog):
    # No manual errors.error_log.clear(): the second compilation must still warn.
    first = _leak_warnings(caplog)
    second = _leak_warnings(caplog)
    assert first, "first compilation should emit the leak warning"
    assert second, "second compilation should warn too -- dedup set must reset"
