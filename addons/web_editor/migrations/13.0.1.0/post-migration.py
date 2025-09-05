import logging
from lxml import etree

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """
    Move ir.ui.view.groups_id into XML attribute 'groups' for QWeb views.
    """

    views = env["ir.ui.view"].with_context(active_test=False).search([
        ("type", "=", "qweb"),
        ("groups_id", "!=", False),
    ])

    for view in views:
        try:
            arch = etree.fromstring(view.arch_db.encode("utf-8"))

            # ambil semua group external_id
            xmlids = [
                "%s.%s" % (g._module or "base", g.id)
                if g.get_external_id().get(g.id)
                else "base.group_user"
                for g in view.groups_id
            ]
            groups_str = ",".join(
                g.get_external_id()[g.id] or "base.group_user" for g in view.groups_id
            )

            # tambahkan atribut groups ke root <t>
            if arch.tag == "t":
                if arch.get("groups"):
                    arch.set("groups", arch.get("groups") + "," + groups_str)
                else:
                    arch.set("groups", groups_str)

            # update arch_db tanpa groups_id
            view.write({
                "arch_db": etree.tostring(arch, encoding="unicode"),
                "groups_id": [(5, 0, 0)],  # clear m2m
            })

            _logger.info("Migrated groups_id from view %s to groups attribute", view.key)

        except Exception as e:
            _logger.error("Failed to migrate view %s: %s", view.key, e)
