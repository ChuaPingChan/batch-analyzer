import os, sys, re, getopt, io, json, tempfile, shelve, subprocess, shutil

class Parser:
    # Regex
    rgxExtrFuncName = re.compile(r'\s*:[ \t]*([a-zA-Z][_a-zA-Z0-9]*)')

    def __init__(self, config_json_file):
        self.config = json.load(config_json_file)

        # Set up logs folder
        self.logsDirPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'logs')
        if os.path.exists(self.logsDirPath) and os.path.isdir(self.logsDirPath):
            shutil.rmtree(self.logsDirPath)
        os.makedirs(self.logsDirPath)

        if self.config['traceLogFilePath']:
            self.traceLogFilePath = self.config['traceLogFilePath']
        else:
            self.traceLogFilePath = os.path.join(self.logsDirPath, 'trace.log')

    def injectEchosAllFiles(self):
        batchFileDirList = self.config['batchFileDirs']

        for batchFileDir in batchFileDirList:
            if not Parser.isGitTrackedDir(batchFileDir):
                print("WARNING: " + batchFileDir + " is not tracked by GIT, skipping it...")
                continue

            for root, dirs, files in os.walk(batchFileDir):
                for file in files:
                    filePath = os.path.join(root, file)
                    if filePath.endswith(".bat") and filePath not in self.config["blacklist"]:
                        self.injectEchosSingleFile(filePath)
        return

    def injectEchosSingleFile(self, filePath):
        assert(filePath.endswith(".bat"))

        print("Injecting trace echos: " + filePath + '...')

        filebasename = os.path.basename(filePath)
        newContentLines = []

        with open(filePath) as file:
            currFuncName = 'main'
            newContentLines.append(self.createEchoStmt(filebasename, currFuncName, isIn=True))

            for line in file:
                stripped_line = line.strip()

                newFuncNameMatchObj = re.match(Parser.rgxExtrFuncName, line.strip())

                if stripped_line[0:5] == "exit ":
                    newContentLines.append(self.createEchoStmt(filebasename, currFuncName, isOut=True))

                newContentLines.append(line)

                if newFuncNameMatchObj:
                    # Just entered a new function/subroutine
                    currFuncName = newFuncNameMatchObj.group(1)
                    newContentLines.append(self.createEchoStmt(filebasename, currFuncName, isIn=True))

        newContentLines.append(self.createEchoStmt(filebasename, currFuncName, isOut=True))

        with open(filePath, 'w') as file:
            file.writelines(newContentLines)

    def createEchoStmt(self, filebasename, funcName='', isIn=False, isOut=False):
        assert (isIn or isOut) and funcName

        direction = 'IN' if isIn else 'OUT'
        msg = 'echo [' + direction + '] ' + filebasename + ' : ' + funcName + r' %*'
        return '\n' + msg + '\n' + msg + ' >> ' + self.traceLogFilePath + '\n'

    @staticmethod
    def isGitTrackedDir(dirPath):
        return subprocess.call(['git', '-C', dirPath, 'status'], stderr=subprocess.STDOUT, stdout = open(os.devnull, 'w')) == 0

    @staticmethod
    def printUsage():
        print("Usage:")
        print('\tpython ' + os.path.basename(__file__) + ' --config="<config_JSON>" --injectEchos')
        print()

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["injectEchos", "config="])
    except getopt.GetoptError:
        Parser.printUsage()
        sys.exit(2)

    if not opts:
        Parser.printUsage()
        sys.exit()

    for opt, arg in opts:
        if opt == "--config":
            configFilePath = arg
    if not configFilePath:
        Parser.printUsage()
        sys.exit()

    with open(configFilePath, 'r') as parser_config_json:
        parser = Parser(parser_config_json)
        for opt, arg in opts:
            if opt == "--injectEchos":
                parser.injectEchosAllFiles()
