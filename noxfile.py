import nox


@nox.session(python=["3.6.8", "2.7"])
def testdataset(session):
    # session.install('pytest')
    session.install("-r", "requirements.txt")
    session.run('./test 1')


@nox.session(python=["3.6.8"])
def testpalpns(session):
    # session.install('pytest')
    session.install("-r", "requirements.txt")
    session.run('./test 2')
    session.run('./test 3')


#@nox.session
# def lint(session):
#    session.install('flake8')
#    session.run('flake8', '--import-order-style', 'google')
