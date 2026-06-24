import logging
from owl_basic import errors
from collections import deque
from owl_basic.syntax.ast import (Repeat, While, ForToStep, Next, Until,
    Endwhile, ReturnFromProcedure, ReturnFromFunction, End, Stop,
    TrueFunc, FalseFunc, LiteralInteger, LiteralFloat)
from owl_basic.exceptions import CompileError
from owl_basic.flow.connectors import connectLoop
from owl_basic.visitor import Visitor

# Why a loop close that the static correlator cannot pair is rejected. Appended to
# the specific diagnostics below so the message says *why* it cannot be compiled.
_DYNAMIC_STACK_NOTE = (
    " BBC BASIC matches loops on a dynamic stack at run time, so a loop opened on "
    "only some paths (e.g. a FOR inside an IF) and closed on another is legal there "
    "but cannot be correlated statically; OWL cannot compile it. Restructure so each "
    "loop is opened and closed unconditionally on the same control-flow path."
)


def _in_id_order(vertices):
    """A deterministic ordering of CFG vertices, by their stable creation id.

    Edges are held in sets of CfgVertex objects, whose iteration order follows
    object identity and so varies from run to run. The loop-correlation verdict
    must not depend on that, so every walk over a vertex's successors goes in id
    order. Ids are assigned at construction, which is deterministic for a given
    parse, so the order -- and the verdict -- is reproducible.
    """
    return sorted(vertices, key=lambda vertex: vertex.id)


def _constant_truth(condition):
    """Whether *condition* is a compile-time constant, and its truth.

    Returns True/False for a constant condition (BBC BASIC: FALSE is 0, TRUE is
    -1, and any non-zero value is true), or None when it is not constant.
    """
    if isinstance(condition, FalseFunc):
        return False
    if isinstance(condition, TrueFunc):
        return True
    if isinstance(condition, (LiteralInteger, LiteralFloat)):
        return condition.value != 0
    return None


def _same_loops(a, b):
    """Two loop stacks are equal iff they hold the same opener nodes in order."""
    return len(a) == len(b) and all(x is y for x, y in zip(a, b))


def _common_prefix(a, b):
    """The longest leading run of opener nodes shared by both loop stacks."""
    prefix = []
    for x, y in zip(a, b):
        if x is not y:
            break
        prefix.append(x)
    return prefix

# Statements that legitimately end a procedure (ENDPROC / =<expr>). Reaching one
# with FOR/REPEAT loops still open is an early exit that the BBC interpreter does
# not unwind: a procedure call saves and restores the hardware and value stacks
# but never the loop stacks, so the open loop's frame leaks. OWL's compiled code
# has no such leak, but the source is poor form, so we warn and name the loops.
_PROCEDURE_EXITS = (ReturnFromProcedure, ReturnFromFunction)

# Statements that end the whole program (END / STOP). Control returns to the
# prompt, which zeroes all loop-level counters, so an open loop here is harmless.
_PROGRAM_EXITS = (End, Stop)

# Either kind is a legitimate terminal, not an unbalanced-loop error.
_EARLY_EXITS = _PROCEDURE_EXITS + _PROGRAM_EXITS


def _describe_open_loop(loop):
    """A short '<KIND> loop opened at line <n>' label for a leaked loop frame."""
    line = getattr(loop, "lineNum", None)
    where = " opened at line %s" % line if line is not None else ""
    if isinstance(loop, ForToStep):
        identifier = getattr(loop, "identifier", None)
        name = getattr(identifier, "identifier", None)
        kind = "FOR %s" % name if name else "FOR"
    elif isinstance(loop, Repeat):
        kind = "REPEAT"
    elif isinstance(loop, While):
        kind = "WHILE"
    else:
        kind = loop.description
    return "%s loop%s" % (kind, where)

class CorrelationVisitor(Visitor):
    """
    This visitor performs abstract execution of the control-flow-graph in order
    to correlate the opening and closing statements or FOR..NEXT, REPEAT..UNTIL
    and WHILE..ENDWHILE loops.
    
    CFG nodes where execution branches are annotated with the current stack of
    loop structures, and a depth first search is performed through the CFG.
    If the stack is non-empty when a terminal node (no out-edges) is encountered
    an error is reported.  If loops are incorrectly nested an error is reported.
    If loops are correctly nested, back-edges are inserted into the CFG.
    """
    
    def __init__(self):
        self.to_visit = deque()
        self.visited = set()
        self.loops = [] # A stack for tracking the current abstract execution state
        # Loops (by id) kept open by a continue-NEXT within the comma chain
        # currently being walked. A later NEXT in the same chain skips them so it
        # matches the next loop out; the flags clear when the chain ends, leaving
        # those loops open for their real close. See visitNext.
        self._continued = set()

    def start(self, entry_point):
        """
        The entry-point from which loop correlation should start
        """
        self._pruneNeverTakenLoopExits(entry_point)
        self.depthFirstSearch(entry_point)
        for v in self.visited:
            if hasattr(v, "loop_stack"):
                del v.loop_stack
            if hasattr(v, "continued_ids"):
                del v.continued_ids

    def _pruneNeverTakenLoopExits(self, entry_point):
        """Remove the fall-through (loop-exit) edge of an `UNTIL FALSE`.

        `UNTIL FALSE` always loops back -- its exit edge is dead. Left in place,
        the correlation DFS propagates a 'loop already closed' stack down that
        dead edge, which corrupts the loop stack for the rest of a loop body that
        has several conditional UNTILs for one REPEAT (the IFS-fractal idiom: an
        inner REPEAT with `IF c ...:UNTIL FALSE` loop-backs and a final `UNTIL
        TRUE` exit). Pruning the dead edge lets each UNTIL correlate to its one
        REPEAT. A genuinely unmatched UNTIL is still reached and still rejected.

        Only a *constant*-false condition is pruned; a non-constant UNTIL can
        exit, so both its edges stay and a real dynamic-stack join still rejects.
        """
        # Collect reachable vertices first; mutating edges mid-walk is unsafe.
        seen = set()
        stack = [entry_point]
        vertices = []
        while stack:
            v = stack.pop()
            if v is None or id(v) in seen:
                continue
            seen.add(id(v))
            vertices.append(v)
            stack.extend(v.outEdges)
        for v in vertices:
            if isinstance(v, Until) and _constant_truth(v.condition) is False:
                for target in list(v.outEdges):
                    v.outEdges.discard(target)
                    target.inEdges.discard(v)

    def depthFirstSearch(self, entry_point):
        self.to_visit.append(entry_point)
        while len(self.to_visit):
            v = self.to_visit.pop()
            # Restore the loop stack
            if hasattr(v, "loop_stack"):
                self.loops = v.loop_stack[:]
                self._continued = set(getattr(v, "continued_ids", ()))
            if v not in self.visited:
                self.visited.add(v)
                v.accept(self)
                if (len(v.outEdges) == 0 and len(v.loopBackEdges) == 0
                        and len(self.loops) != 0):
                    if isinstance(v, _PROCEDURE_EXITS):
                        # ENDPROC / =<expr> reached with loops still open: legal,
                        # but it leaks those loop frames in the BBC interpreter.
                        self._warnUnceremoniousExit(v)
                    elif not isinstance(v, _PROGRAM_EXITS):
                        # Falls off the end of the program (or routine) with loops
                        # still open -- an early exit from a loop (e.g. a
                        # conditional NEXT/UNTIL not taken on this path). The loop
                        # is still correlated by its own NEXT/UNTIL on the path
                        # that closes it; this path simply leaves it open. In BBC
                        # BASIC the frame leaks until control returns to the
                        # prompt; OWL's compiled code has no such frame. This is
                        # the same benign leak as an ENDPROC/= exiting a loop, not
                        # a dynamic-stack error, so warn rather than reject.
                        self._warnLeakedLoopsAtEnd(v)
                # Propagate the loop stack as it stands *after* this statement
                # (accept() above pushed/popped it) to every successor, recording
                # it on the target so the state is restored when that target is
                # later visited. outEdges is an unordered set, so walk it in a
                # deterministic (id) order: the first path to reach a join records
                # its stack there, and which path that is must not vary run to run.
                # If two paths reach a join with different loop nesting, the
                # program relies on the dynamic loop stack and cannot be compiled.
                outgoing = self.loops[:]
                ordered_targets = _in_id_order(v.outEdges)
                for target in ordered_targets:
                    self._propagateLoopStack(v, target, outgoing)
                    # Carry the continue flags alongside the stack. They are empty
                    # except inside a comma chain (which has no joins), so the
                    # first writer wins, like loop_stack.
                    if not hasattr(target, "continued_ids"):
                        target.continued_ids = set(self._continued)
                self.to_visit.extend(ordered_targets)

    def _propagateLoopStack(self, source, target, loops):
        """Record *loops* as target's entry stack, resolving benign leaks.

        Two paths may reach a join with different loop nesting. When one stack is
        a prefix of the other and the join is not itself a loop-closing statement,
        the extra inner loop(s) were left via an early forward exit (e.g. GOTO out
        of a FOR): their frames leak, but each loop is still correlated by its own
        NEXT on the path that does not jump out. Continue with the loops open on
        *every* path (the common prefix). A genuine divergence -- a loop opened on
        only some paths and then *closed* at this join (NEXT/UNTIL/ENDWHILE), or
        stacks that are not prefix-related -- relies on the dynamic loop stack and
        cannot be compiled.
        """
        existing = getattr(target, "loop_stack", None)
        if existing is None:
            target.loop_stack = loops
            return
        if _same_loops(existing, loops):
            return
        common = _common_prefix(existing, loops)
        prefix_related = len(common) == min(len(existing), len(loops))
        closes_a_loop = isinstance(target, (Next, Until, Endwhile))
        if prefix_related and not closes_a_loop:
            target.loop_stack = common  # the loops open on all paths; extras leak
            return
        raise CompileError(
            "Control flow reaching line %s is inside different loops "
            "depending on the path taken to get there, so a loop is opened on "
            "one path but not another.%s"
            % (target.lineNum, _DYNAMIC_STACK_NOTE))

    def _warnUnceremoniousExit(self, exit_stmt):
        """Warn that *exit_stmt* leaves one or more loops open as it returns.

        The loops are listed innermost-first, matching the order the BBC
        interpreter would have unwound them had they terminated normally.
        """
        exit_kind = ("ENDPROC" if isinstance(exit_stmt, ReturnFromProcedure)
                     else "function return '='")
        open_loops = ", ".join(_describe_open_loop(loop)
                               for loop in reversed(self.loops))
        errors.warning(
            "%s at line %s exits while still inside the %s. In BBC BASIC a "
            "loop's stack frame is reclaimed only by its own NEXT/UNTIL/ENDWHILE "
            "(or by returning to the prompt), so leaving it through a procedure "
            "exit leaks that frame. OWL's compiled code does not leak, but this "
            "is poor form: restructure so the loop terminates normally -- fold "
            "the early-exit test into the UNTIL, or set the FOR index to its "
            "limit." % (exit_kind, exit_stmt.lineNum, open_loops))

    def _warnLeakedLoopsAtEnd(self, terminal):
        """Warn that control falls off the end with one or more loops still open.

        Listed innermost-first, matching the order the BBC interpreter would have
        unwound them. Each loop is correlated by its own NEXT/UNTIL on the path
        that closes it; this path just leaves it open (a benign leaked frame).
        """
        open_loops = ", ".join(_describe_open_loop(loop)
                               for loop in reversed(self.loops))
        errors.warning(
            "execution falls off the end at line %s while still inside the %s. "
            "The loop is closed by its NEXT/UNTIL on the path that takes it; on "
            "this path it is left open, which leaks the loop's stack frame in BBC "
            "BASIC (OWL's compiled code does not leak)."
            % (terminal.lineNum, open_loops))

    def visitAstStatement(self, statement):
        """
        Do nothing for most AST statements
        """
        pass
    
    def visitRepeat(self, repeat_stmt):
        self.loops.append(repeat_stmt)
        
    def visitUntil(self, until_stmt):
        while True:
            idx = self._topmost_open()
            if idx < 0:
                raise CompileError(
                    "UNTIL at line %d has no REPEAT loop to close.%s"
                    % (until_stmt.lineNum, _DYNAMIC_STACK_NOTE))
            peek = self.loops[idx]
            if not isinstance(peek, Repeat):
                # UNTIL closes a REPEAT; an inner loop of another kind above it is
                # abandoned (BBC unwinds to the matching opener). Skip and leak it.
                del self.loops[idx]
                continue
            connectLoop(until_stmt, peek)
            # `IF c UNTIL FALSE` is the REPEAT continue idiom (its dead exit edge
            # is pruned, so it is a pure back-edge). Keep the loop open if so.
            if self._closer_continues_loop(until_stmt, peek):
                self._continued.add(id(peek))
            else:
                del self.loops[idx]
            break
        self._clear_continue_chain_flags(until_stmt)
        
    def visitWhile(self, while_stmt):
        self.loops.append(while_stmt)
        
    def visitEndwhile(self, endwhile_stmt):
        while True:
            idx = self._topmost_open()
            if idx < 0:
                raise CompileError(
                    "ENDWHILE at line %d has no WHILE loop to close.%s"
                    % (endwhile_stmt.lineNum, _DYNAMIC_STACK_NOTE))
            peek = self.loops[idx]
            if not isinstance(peek, While):
                # ENDWHILE closes a WHILE; an inner loop of another kind above it
                # is abandoned (BBC unwinds to the matching opener). Skip/leak it.
                del self.loops[idx]
                continue
            connectLoop(endwhile_stmt, peek)
            # `IF c ENDWHILE` is the BASIC V continue idiom: a back-edge to the
            # WHILE test, with a later ENDWHILE the real close. Keep it open if so.
            if self._closer_continues_loop(endwhile_stmt, peek):
                self._continued.add(id(peek))
            else:
                # The real close: record the pairing so codegen can branch the
                # WHILE's pre-test past this ENDWHILE to the after-loop block.
                peek.closingEndwhile = endwhile_stmt
                del self.loops[idx]
            break
        self._clear_continue_chain_flags(endwhile_stmt)
        
    def visitForToStep(self, for_stmt):
        self.loops.append(for_stmt)
        
    def _closer_continues_loop(self, closer, opener):
        """Whether *closer* is a *continue* for *opener*, not its exit.

        A loop may have several closers -- the BBC continue idioms: `IF c NEXT`,
        `IF c ENDWHILE` (and, via UNTIL-FALSE exit pruning, `IF c UNTIL FALSE`).
        When the condition holds the closer is a back-edge -- skip the rest of
        the body, start the next iteration -- and a *later* closer performs the
        real exit. The exit closer's fall-through instead leaves the loop,
        reachable only *through* that closer.

        Structural test, independent of CFG walk order: the opener can reach this
        closer's fall-through point -- past any `NEXT,,` comma run it belongs to
        -- *without passing through it*. A loop with one closer, or whose last
        closer exits the body, is never a continue; a conditionally-*opened* loop
        is a different shape that reaches a closing join with divergent nesting
        and is rejected there, so this is consulted only once a closer genuinely
        matches an open loop.
        """
        # Walk the run of NEXT vertices that form ONE `NEXT,,` statement to where
        # it falls through, then ask whether the FOR re-enters there. A genuine
        # comma component is reached SOLELY from its predecessor (single in-edge);
        # a NEXT reached from elsewhere (a join) is a *separate* closer -- e.g. a
        # conditional `IF c NEXT` whose fall-through meets a later `NEXT` that the
        # IF's other branch also reaches -- and the body re-enters there, so the
        # chain ends and that separate NEXT is the re-entry point.
        chain = set()
        cursor = closer
        while True:
            chain.add(id(cursor))
            out = list(cursor.outEdges)
            if len(out) != 1:
                break                      # terminal exit or branch: chain ends
            nxt = out[0]
            if isinstance(nxt, Next) and len(nxt.inEdges) == 1:
                cursor = nxt               # genuine NEXT, comma component; walk on
                continue
            cursor = nxt                   # separate closer / ordinary re-entry
            break
        seen = set(chain)
        stack = [opener]
        while stack:
            v = stack.pop()
            if id(v) in seen:
                continue
            seen.add(id(v))
            if v is cursor:
                return True
            stack.extend(v.outEdges)
        return False

    def _topmost_open(self):
        """Index of the innermost loop not already continued in this comma chain.

        A continue closer leaves its loop on the stack (flagged in
        self._continued) so a following NEXT in the same `NEXT,`/`NEXT,,` chain
        matches the next loop out, not the one just continued.
        """
        idx = len(self.loops) - 1
        while idx >= 0 and id(self.loops[idx]) in self._continued:
            idx -= 1
        return idx

    def _clear_continue_chain_flags(self, closer):
        """Clear the continue flags on leaving a `NEXT,,` comma chain.

        Only a genuine comma component -- a single NEXT successor reached solely
        from here -- keeps the flags; a separate following closer (a join, e.g. a
        real closing NEXT after a conditional continue) ends the chain, so the
        continued loops are open again here.
        """
        outs = list(closer.outEdges)
        in_comma_chain = (len(outs) == 1 and isinstance(outs[0], Next)
                          and len(outs[0].inEdges) == 1)
        if not in_comma_chain:
            self._continued = set()

    def visitNext(self, next_stmt):
        logging.debug("NEXT statement = %s", next_stmt)
        #logging.debug("NEXT identifiers = %s", next_stmt.identifiers[0].identifier)
        while True:
            idx = self._topmost_open()
            if idx < 0:
                raise CompileError(
                    "NEXT at line %d has no FOR loop to close.%s"
                    % (next_stmt.lineNum, _DYNAMIC_STACK_NOTE))
            peek = self.loops[idx]
            if not isinstance(peek, ForToStep):
                # NEXT closes a FOR; an inner loop of another kind sitting above
                # it is abandoned -- BBC unwinds the run-time stack to the
                # matching opener, leaking the skipped frame. Skip it and look
                # deeper. (If no FOR is found at all, idx falls below 0 above and
                # the "no FOR to close" error fires.)
                del self.loops[idx]
                continue

            for_stmt = self.loops[idx]
            # If the next_stmt has no attached identifiers, it applies to the
            # top FOR statement on the stack
            if len(next_stmt.identifiers) == 0:
                 next_stmt.identifiers.append(for_stmt.identifier)
            id1 = for_stmt.identifier.identifier
            logging.debug("next_stmt identifiers: %s", next_stmt.identifiers)
            id2 = next_stmt.identifiers[0].identifier
            logging.debug("self.loops = %s", self.loops)
            logging.debug("id1 = %s", id1)
            logging.debug("id2 = %s", id2)
            # TODO: Check that the symbols are equal, not just the names
            if for_stmt.identifier.identifier == next_stmt.identifiers[0].identifier:
                connectLoop(next_stmt, for_stmt)
                if self._closer_continues_loop(next_stmt, for_stmt):
                    # The BBC continue idiom: this NEXT loops back, but the loop
                    # is closed by a later NEXT. Record the back-edge and keep the
                    # loop open (flagged), so a following NEXT in the same comma
                    # chain matches the next loop, and the real close still
                    # correlates -- its fall-through into the body does not
                    # spuriously empty the stack.
                    self._continued.add(id(for_stmt))
                else:
                    del self.loops[idx]
                break
            # A named NEXT closing an outer loop: the skipped inner loop leaks.
            del self.loops[idx]
        self._clear_continue_chain_flags(next_stmt)
    
        
        