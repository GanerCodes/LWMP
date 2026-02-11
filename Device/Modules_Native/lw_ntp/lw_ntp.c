#include "py/obj.h"
#include "py/runtime.h"
#include "py/mpthread.h"
#include <stdint.h>
#include <string.h>
#include <sys/socket.h>
#include <netdb.h>
#include <unistd.h>
#include <arpa/inet.h>
#include "esp_timer.h"

static mp_obj_t lw_ntp_ntp_raw(size_t n_args, const mp_obj_t *args) { // AI
    const char *host = mp_obj_str_get_str(args[0]);
    int timeout = mp_obj_get_int(args[1]);

    int sock = -1;
    int64_t T0 = -1;
    int64_t T3 = -1;
    uint8_t buf[48];
    memset(buf, 0, sizeof(buf));

    struct sockaddr_in addr;
    struct hostent *he;

    MP_THREAD_GIL_EXIT();
    sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock < 0) goto end;

    if (timeout != -1) {
        struct timeval tv;
        tv.tv_sec = timeout;
        tv.tv_usec = 0;
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv)); }

    he = gethostbyname(host);
    if (!he) goto end;

    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(123);
    memcpy(&addr.sin_addr, he->h_addr, he->h_length);

    uint8_t pkt[48];
    memset(pkt, 0, 48);
    pkt[0] = 0x1B;

    T0 = esp_timer_get_time();
    if (   sendto(sock, pkt, 48, 0, (struct sockaddr *)&addr, sizeof(addr)) < 0
        || recv(sock, buf, 48, 0) < 0)
      goto end;
    T3 = esp_timer_get_time();
end:
    if (sock >= 0) close(sock);
    MP_THREAD_GIL_ENTER();
    if(T0 < 0 || T3 < 0)
        return mp_obj_new_tuple(3, (mp_obj_t[]){
            mp_obj_new_int(-1),
            mp_obj_new_int(-1),
            mp_obj_new_bytes(buf, 48) });
    return mp_obj_new_tuple(3, (mp_obj_t[]){
        mp_obj_new_int_from_ll(T0),
        mp_obj_new_int_from_ll(T3),
        mp_obj_new_bytes(buf, 48) }); }
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(lw_ntp_ntp_raw_obj, 2, 2, lw_ntp_ntp_raw);

static const mp_rom_map_elem_t lw_ntp_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_lw_ntp) },
    { MP_ROM_QSTR(MP_QSTR_ntp_raw), MP_ROM_PTR(&lw_ntp_ntp_raw_obj) },
};

static MP_DEFINE_CONST_DICT(lw_ntp_module_globals, lw_ntp_module_globals_table);

const mp_obj_module_t lw_ntp_user_c_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&lw_ntp_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_lw_ntp, lw_ntp_user_c_module);