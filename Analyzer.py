import os, sys, getopt, shelve

class Analyzer:

    def __init__(self):
        self.batchFiles2Idx = dict()
        self.idx2BatchFiles = dict()
        self.funcs2Idx = dict()
        self.idx2Funcs = dict()
        self.fileIdx2funcIdxs = dict()
        self.funcIdx2fileIdxs = dict()
        self.caller2callee = dict()
        self.callee2caller = dict()

        self.loadCachedIndexes()

    def loadCachedIndexes(self, cacheDir="cache", cacheName="index"):
        assert os.path.exists(cacheDir) and os.path.isdir(cacheDir), "Index not found at " + cacheDir

        indexCache = shelve.open(os.path.join(cacheDir, cacheName))

        self.batchFiles2Idx = indexCache["batchFiles2Idx"]
        self.idx2BatchFiles = indexCache["idx2BatchFiles"]
        self.funcs2Idx = indexCache["funcs2Idx"]
        self.idx2Funcs = indexCache["idx2Funcs"]
        self.fileIdx2funcIdxs = indexCache["fileIdx2funcIdxs"]
        self.funcIdx2fileIdxs = indexCache["funcIdx2fileIdxs"]
        self.caller2callee = indexCache["caller2callee"]
        self.callee2caller = indexCache["callee2caller"]

        indexCache.close()

    def printFuncDependencyTree(self, funcName):
        if funcName not in self.funcs2Idx:
            print('WARNING: Function ' + funcName + ' is not found in index')
            return

        funcIdx = self.funcs2Idx[funcName]
        self.printFuncDependencyTreeRecursive([funcIdx])

    def printFuncDependencyTreeRecursive(self, callStack, processedFuncIdxs=set()):
        """
        Recursively walks through and prints the call hierarchy of the caller function at the top of the callStack
        """
        assert callStack

        funcIdx = callStack[-1]
        depth = len(callStack) - 1
        print('--' * depth + str(self.getParentBaseFiles(funcIdx)) + ' ' + self.idx2Funcs[funcIdx])
        if funcIdx in processedFuncIdxs:
            # Base case 1: This function's call hierarchy has been processed (memoization)
            print('--' * (depth + 1) + '... (Truncated: Sub-hierarchy processed before)')
            callStack.pop(-1)
            return
        else:
            processedFuncIdxs.add(funcIdx)

        # Base case 2: This function doesn't have callers
        if funcIdx not in self.callee2caller:
            callStack.pop(-1)
            return
        else:
            callerIdxSet = self.callee2caller[funcIdx]
            assert callerIdxSet

        for callerIdx in callerIdxSet:
            if callerIdx not in callStack:
                callStack.append(callerIdx)
                self.printFuncDependencyTreeRecursive(callStack, processedFuncIdxs)
            else:
                # Base case 3: Recursion cycle detected
                # TODO: This base case may be redundant and never be reached because of base case 1. Can consider removing.
                print('--' * (depth + 1) + str(self.getParentBaseFiles(callerIdx)) + ' ' + self.idx2Funcs[callerIdx] + '(recursion)')
                callStack.pop(-1)
                return

        # Base case 4: Finished printing all callers
        callStack.pop(-1)
        return

    def getParentBaseFiles(self, funcIdx):
        res = []
        fileIdxs = self.funcIdx2fileIdxs[funcIdx]
        for fileIdx in fileIdxs:
            res.append(os.path.basename(self.idx2BatchFiles[fileIdx]))
        return res

    def printCallTrace(self, funcName):
        if funcName not in self.funcs2Idx:
            print('WARNING: Function ' + funcName + ' is not found in index')
            return

        funcIdx = self.funcs2Idx[funcName]
        self.printCallTraceRecursive([funcIdx])

    def printCallTraceRecursive(self, callStack, processedFuncIdxs=set()):
        """
        Recursively walks through and prints the call hierarchy of the callee function at the top of the callStack
        """
        assert callStack

        funcIdx = callStack[-1]
        depth = len(callStack) - 1
        print('--' * depth + str(self.getParentBaseFiles(funcIdx)) + ' ' + self.idx2Funcs[funcIdx])
        if funcIdx in processedFuncIdxs:
            # Base case 1: This function's call hierarchy has been processed (memoization)
            print('--' * (depth + 1) + '... (Truncated: Sub-hierarchy processed before)')
            callStack.pop(-1)
            return
        else:
            processedFuncIdxs.add(funcIdx)

        calleeList = self.caller2callee[funcIdx]
        for calleeIdx in calleeList:
            if calleeIdx not in callStack:
                callStack.append(calleeIdx)
                self.printCallTraceRecursive(callStack, processedFuncIdxs)
            else:
                # Base case 2: Recursion cycle detected
                # TODO: This base case may be redundant and never be reached because of base case 1. Can consider removing.
                print('--' * (depth + 1) + str(self.getParentBaseFiles(calleeIdx)) + ' ' + self.idx2Funcs[calleeIdx] + '(recursion)')
                callStack.pop(-1)
                return

        # Base case 3: Finished printing all callees
        callStack.pop(-1)
        return

    @staticmethod
    def printUsage():
        print("Usage:")
        print('\tpython ' + os.path.basename(__file__) + ' [--callHierarchy | --trace] <funcName>')
        print()

if __name__ == '__main__':
    # Validate and handle cmd arguments
    if len(sys.argv) < 2:
        Analyzer.printUsage()
        sys.exit()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["callHierarchy", "trace"])
    except getopt.GetoptError:
        Analyzer.printUsage()
        sys.exit(2)

    if len(opts) > 1:
        Analyzer.printUsage()
        sys.exit(2)

    # Main routine
    funcName = sys.argv[-1]
    analyzer = Analyzer()

    for opt, arg in opts:
        if opt == "--callHierarchy":
            analyzer.printFuncDependencyTree(funcName)
        elif opt == "--trace":
            analyzer.printCallTrace(funcName)
        else:
            Analyzer.printUsage()
