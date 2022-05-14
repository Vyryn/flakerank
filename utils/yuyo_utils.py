import hikari
import yuyo


async def delete_button_callback(ctx: yuyo.ComponentContext) -> None:
    """Constant callback used by delete buttons.

    Parameters
    ----------
    ctx : yuyo.ComponentContext
        The context that triggered this delete.
    """
    author_ids = set(map(hikari.Snowflake, ctx.interaction.custom_id.removeprefix(DELETE_CUSTOM_ID).split(",")))
    if (
        ctx.interaction.user.id in author_ids
        or ctx.interaction.member
        and author_ids.intersection(ctx.interaction.member.role_ids)
    ):
        await ctx.defer(hikari.ResponseType.DEFERRED_MESSAGE_UPDATE)
        await ctx.delete_initial_response()

    else:
        await ctx.create_initial_response(
            hikari.ResponseType.MESSAGE_CREATE, "You do not own this message", flags=hikari.MessageFlag.EPHEMERAL
        )


DELETE_CUSTOM_ID = "AUTHOR_DELETE_BUTTON:"
