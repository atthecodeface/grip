class TestResult:
    def __init__(self, reason):
        pass
    pass
OptTestResult = Optional[TestResult]

class Tests:
    tests: List[thing]
    def __init__(self):
        self.tests = []
        pass
    def run(self, env) -> OptTestResult:
        for a in self.tests:
            a_result = a.execute(env, self)
            if a_result is not None:
                return a_result
            pass
        return None
    pass
class Shell:
    cmd : str
    wd  : Optional[str]
    rc : int
    stdout : str
    stderr : str

class Test:
    def __init__(self, cmd, wd=None, rc:Optional[int]=None, stdout_re:Optionals[str]=None, stderr_re=Options[str]=None):
        self.shell = ()
        pass
    def execute(self, env, tests:Tests) -> OptTestResult:
        self.shell.run()
        return None
    pass

class TestGetCs(Test)
    def __init__(self, **kwargs):
        Test.__init__(self, **kwargs)
        pass
    def execute(self, **kwargs):
        result =Test.execute(self, **kwards)
        if result is not None: return result
        cs = shell.stdout.strip()
        pass

class bana(Tests):
    tests = [ Test("cat banana", stdout_re=r"banana"),
              ]

pass
