import datetime
import time, os

def printError (szTexto):
    dateToday = datetime.datetime.now()
    dateString=dateToday.strftime ("%Y-%m-%d %H:%M:%S")
    
    filedateString=dateToday.strftime ("%Y%m%d")
    
    szLogMessage= dateString+' '+ szTexto+'\n'
    
    szFileName='../logs/' + filedateString + '_mainlog'

    fd = open(szFileName, 'a') # el mismo fichero
    fd.write (szLogMessage)
        
    fd.close()

def printErrorAPI (szTexto, webPython):
    dateToday = datetime.datetime.now()
    dateString=dateToday.strftime ("%Y-%m-%d %H:%M:%S")
    
    filedateString=dateToday.strftime ("%Y%m%d")
    
    szLogMessage= dateString+' '+ szTexto+'\n'
    
    if (webPython == 0):
        szFileName='../logs/' + filedateString + '_AirzoneAPIweb'
    else:
        szFileName='../logs/' + filedateString + '_AirzoneAPI'

    fd = open(szFileName, 'a') # el mismo fichero
    fd.write (szLogMessage)
        
    fd.close()
    
def main():

    printError('Prueba')
    
if __name__ == "__main__":
    main()
