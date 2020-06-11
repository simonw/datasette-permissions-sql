from datasette import hookimpl
import json


@hookimpl
def permission_allowed(datasette, actor, action, resource):
    actor = actor or {}

    async def inner():
        params = {"action": action}
        if resource:
            if len(resource) == 2:
                resource_1, resource_2 = resource
            else:
                resource_1, resource_2 = resource, None
            params["resource_1"] = resource_1
            params["resource_2"] = resource_2
        for key, value in actor.items():
            if isinstance(value, (dict, list, tuple)):
                value = json.dumps(value, default=repr)
            params["actor_{}".format(key)] = value
        for rule in datasette.plugin_config("datasette-permissions-sql") or []:
            sql = rule["sql"]
            rule_action = rule.get("action")
            rule_resource = rule.get("resource")
            if isinstance(rule_resource, list):
                rule_resource = tuple(rule_resource)
            fallback = rule.get("fallback")
            # Optionally match on action/resource
            if rule_action is not None and rule_action != action:
                continue
            if rule_resource is not None and rule_resource != resource:
                continue
            # Execute the SQL
            if actor:
                db = datasette.get_database(rule.get("database"))
                result = await db.execute(sql, params)
                row = result.first()
            else:
                row = None
            if row is None:
                if not fallback:
                    # Explicit deny
                    return False
                else:
                    # Fallback mode: try next rule in the loop
                    continue
            if len(row) == 1 and str(row[0]) == "-1":
                # Explicit deny
                return False
            else:
                return True

    return inner
