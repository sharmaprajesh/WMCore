"""
_InsertComponent_

MySQL implementation of UpdateWorker
"""

__all__ = []



import time
from WMCore.Database.DBFormatter import DBFormatter

class UpdateWorker(DBFormatter):

    sqlpart1 = """UPDATE wm_workers
                      SET last_updated = :last_updated
               """
    sqlpart3 = """ WHERE component_id = :component_id
                   AND name = :worker_name"""

    def execute(self, componentID, workerName, state = None, timeSpent=None,
                results=None, conn = None, transaction = False):

        binds = {"component_id": componentID,
                 "worker_name": workerName,
                 "last_updated": int(time.time())}

        sqlpart2 = ""
        if state:
            binds["state"] = state
            sqlpart2 += ", state = :state"
        if timeSpent:
            binds["cycle_time"] = timeSpent
            sqlpart2 += ", cycle_time = :cycle_time"
        if results:
            binds["outcome"] = results
            sqlpart2 += ", outcome = :outcome"

        sql = self.sqlpart1 + sqlpart2 + self.sqlpart3

        self.dbi.processData(sql, binds, conn = conn,
                             transaction = transaction)
        return
