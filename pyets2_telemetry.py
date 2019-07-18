import telemetry

SCS_TELEMETRY_CHANNEL_game_time = "game.time"

SCS_TELEMETRY_CHANNEL_FLAG_none         = 0x00000000
SCS_TELEMETRY_CHANNEL_FLAG_each_frame   = 0x00000001
SCS_TELEMETRY_CHANNEL_FLAG_no_value     = 0x00000002

# Index
SCS_U32_NIL = -1

SCS_VALUE_TYPE_u32 = 3

def channel_cb(name, index, value, context):
    telemetry.log("Got CB: %s, %u, %u, %s" % (name, index, value, repr(context)))

def telemetry_init(version, game_name, game_id, game_version):
    telemetry.log("%u, %s, %s, %u" % (version, game_name, game_id, game_version))
    telemetry.log("1")
    ret = telemetry.register_for_channel(SCS_TELEMETRY_CHANNEL_game_time,
                                         SCS_U32_NIL,
                                         SCS_VALUE_TYPE_u32,
                                         SCS_TELEMETRY_CHANNEL_FLAG_none,
                                         channel_cb, "my context")
    telemetry.log("Register return: %u" % ret);


def telemetry_shutdown():
    telemetry.log("bye")
