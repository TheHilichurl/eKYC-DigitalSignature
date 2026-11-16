.class public Lcom/ekyc/digitalsignature/SecurityGuard;
.super Ljava/lang/Object;
.source "SecurityGuard.java"

.field private static final ENC_PROC_MAPS:[B
.field private static final ENC_FRIDA:[B
.field private static final ENC_XPOSED:[B
.field private static final ENC_LOCALHOST:[B
.field private static final ENC_SU1:[B
.field private static final ENC_SU2:[B
.field private static final ENC_SU3:[B
.field private static final ENC_TEST_KEYS:[B

.method static constructor <clinit>()V
    .registers 2

    # /proc/self/maps
    const/16 v0, 0xf
    new-array v0, v0, [B
    fill-array-data v0, :array_proc_maps
    sput-object v0, Lcom/ekyc/digitalsignature/SecurityGuard;->ENC_PROC_MAPS:[B

    # frida
    const/4 v0, 0x5
    new-array v0, v0, [B
    fill-array-data v0, :array_frida
    sput-object v0, Lcom/ekyc/digitalsignature/SecurityGuard;->ENC_FRIDA:[B

    # xposed
    const/4 v0, 0x6
    new-array v0, v0, [B
    fill-array-data v0, :array_xposed
    sput-object v0, Lcom/ekyc/digitalsignature/SecurityGuard;->ENC_XPOSED:[B

    # 127.0.0.1
    const/16 v0, 0x9
    new-array v0, v0, [B
    fill-array-data v0, :array_localhost
    sput-object v0, Lcom/ekyc/digitalsignature/SecurityGuard;->ENC_LOCALHOST:[B

    # /system/bin/su
    const/16 v0, 0xe
    new-array v0, v0, [B
    fill-array-data v0, :array_su1
    sput-object v0, Lcom/ekyc/digitalsignature/SecurityGuard;->ENC_SU1:[B

    # /system/xbin/su
    const/16 v0, 0xf
    new-array v0, v0, [B
    fill-array-data v0, :array_su2
    sput-object v0, Lcom/ekyc/digitalsignature/SecurityGuard;->ENC_SU2:[B

    # /sbin/su
    const/16 v0, 0x8
    new-array v0, v0, [B
    fill-array-data v0, :array_su3
    sput-object v0, Lcom/ekyc/digitalsignature/SecurityGuard;->ENC_SU3:[B

    # test-keys
    const/16 v0, 0x9
    new-array v0, v0, [B
    fill-array-data v0, :array_test_keys
    sput-object v0, Lcom/ekyc/digitalsignature/SecurityGuard;->ENC_TEST_KEYS:[B

    return-void

    :array_proc_maps
    .array-data 1
        0x75t 0x2at 0x28t 0x35t 0x39t 0x75t 0x29t 0x3ft 0x36t 0x3ct 0x75t 0x37t 0x3bt 0x2at 0x29t
    .end array-data

    :array_frida
    .array-data 1
        0x3ct 0x28t 0x33t 0x3et 0x3bt
    .end array-data

    :array_xposed
    .array-data 1
        0x22t 0x2at 0x35t 0x29t 0x3ft 0x3et
    .end array-data

    :array_localhost
    .array-data 1
        0x6bt 0x68t 0x6dt 0x74t 0x6at 0x74t 0x6at 0x74t 0x6bt
    .end array-data

    :array_su1
    .array-data 1
        0x75t 0x29t 0x23t 0x29t 0x2et 0x3ft 0x37t 0x75t 0x38t 0x33t 0x34t 0x75t 0x29t 0x2ft
    .end array-data

    :array_su2
    .array-data 1
        0x75t 0x29t 0x23t 0x29t 0x2et 0x3ft 0x37t 0x75t 0x22t 0x38t 0x33t 0x34t 0x75t 0x29t 0x2ft
    .end array-data

    :array_su3
    .array-data 1
        0x75t 0x29t 0x38t 0x33t 0x34t 0x75t 0x29t 0x2ft
    .end array-data

    :array_test_keys
    .array-data 1
        0x2et 0x3ft 0x29t 0x2et 0x77t 0x31t 0x3ft 0x23t 0x29t
    .end array-data
.end method

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method

# Anti-Reverse Engineering: String Decryption helper
.method public static decryptString([B)Ljava/lang/String;
    .registers 5
    array-length v0, p0
    new-array v1, v0, [B
    const/4 v2, 0x0

    :goto_4
    if-ge v2, v0, :cond_13
    aget-byte v3, p0, v2
    xor-int/lit8 v3, v3, 0x5a
    int-to-byte v3, v3
    aput-byte v3, v1, v2
    add-int/lit8 v2, v2, 0x1
    goto :goto_4

    :cond_13
    new-instance v0, Ljava/lang/String;
    invoke-direct {v0, v1}, Ljava/lang/String;-><init>([B)V
    return-object v0
.end method

# Anti-Root Detection with obfuscated strings
.method public static isRooted()Z
    .registers 5
    const/4 v0, 0x1
    const/4 v1, 0x0

    new-instance v2, Ljava/io/File;
    sget-object v3, Lcom/ekyc/digitalsignature/SecurityGuard;->ENC_SU1:[B
    invoke-static {v3}, Lcom/ekyc/digitalsignature/SecurityGuard;->decryptString([B)Ljava/lang/String;
    move-result-object v3
    invoke-direct {v2, v3}, Ljava/io/File;-><init>(Ljava/lang/String;)V
    invoke-virtual {v2}, Ljava/io/File;->exists()Z
    move-result v2
    if-eqz v2, :cond_14
    return v0

    :cond_14
    new-instance v2, Ljava/io/File;
    sget-object v3, Lcom/ekyc/digitalsignature/SecurityGuard;->ENC_SU2:[B
    invoke-static {v3}, Lcom/ekyc/digitalsignature/SecurityGuard;->decryptString([B)Ljava/lang/String;
    move-result-object v3
    invoke-direct {v2, v3}, Ljava/io/File;-><init>(Ljava/lang/String;)V
    invoke-virtual {v2}, Ljava/io/File;->exists()Z
    move-result v2
    if-eqz v2, :cond_26
    return v0

    :cond_26
    new-instance v2, Ljava/io/File;
    sget-object v3, Lcom/ekyc/digitalsignature/SecurityGuard;->ENC_SU3:[B
    invoke-static {v3}, Lcom/ekyc/digitalsignature/SecurityGuard;->decryptString([B)Ljava/lang/String;
    move-result-object v3
    invoke-direct {v2, v3}, Ljava/io/File;-><init>(Ljava/lang/String;)V
    invoke-virtual {v2}, Ljava/io/File;->exists()Z
    move-result v2
    if-eqz v2, :cond_38
    return v0

    :cond_38
    # Check test-keys in Build.TAGS
    sget-object v2, Landroid/os/Build;->TAGS:Ljava/lang/String;
    if-eqz v2, :cond_49
    sget-object v3, Lcom/ekyc/digitalsignature/SecurityGuard;->ENC_TEST_KEYS:[B
    invoke-static {v3}, Lcom/ekyc/digitalsignature/SecurityGuard;->decryptString([B)Ljava/lang/String;
    move-result-object v3
    invoke-virtual {v2, v3}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_49
    return v0

    :cond_49
    return v1
.end method

# Anti-Hooking & Anti-Frida Detection with encrypted signatures
.method public static isFridaOrHookDetected()Z
    .registers 6
    const/4 v0, 0x1
    const/4 v1, 0x0

    # 1. Check proc maps for frida or xposed hooks
    :try_start_3
    new-instance v2, Ljava/io/BufferedReader;
    new-instance v3, Ljava/io/FileReader;
    sget-object v4, Lcom/ekyc/digitalsignature/SecurityGuard;->ENC_PROC_MAPS:[B
    invoke-static {v4}, Lcom/ekyc/digitalsignature/SecurityGuard;->decryptString([B)Ljava/lang/String;
    move-result-object v4
    invoke-direct {v3, v4}, Ljava/io/FileReader;-><init>(Ljava/lang/String;)V
    invoke-direct {v2, v3}, Ljava/io/BufferedReader;-><init>(Ljava/io/Reader;)V

    sget-object v3, Lcom/ekyc/digitalsignature/SecurityGuard;->ENC_FRIDA:[B
    invoke-static {v3}, Lcom/ekyc/digitalsignature/SecurityGuard;->decryptString([B)Ljava/lang/String;
    move-result-object v3

    sget-object v4, Lcom/ekyc/digitalsignature/SecurityGuard;->ENC_XPOSED:[B
    invoke-static {v4}, Lcom/ekyc/digitalsignature/SecurityGuard;->decryptString([B)Ljava/lang/String;
    move-result-object v4

    :cond_1f
    invoke-virtual {v2}, Ljava/io/BufferedReader;->readLine()Ljava/lang/String;
    move-result-object v5
    if-eqz v5, :cond_36
    invoke-virtual {v5, v3}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v5
    if-nez v5, :cond_32
    invoke-virtual {v2}, Ljava/io/BufferedReader;->readLine()Ljava/lang/String;
    move-result-object v5
    if-eqz v5, :cond_1f
    invoke-virtual {v5, v4}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v5
    if-eqz v5, :cond_1f

    :cond_32
    invoke-virtual {v2}, Ljava/io/BufferedReader;->close()V
    return v0

    :cond_36
    invoke-virtual {v2}, Ljava/io/BufferedReader;->close()V
    :try_end_39
    .catch Ljava/lang/Exception; {:try_start_3 .. :try_end_39} :catch_3a

    goto :goto_3b

    :catch_3a
    move-exception v2

    :goto_3b
    # 2. Check Frida default server port 27042
    :try_start_3b
    new-instance v2, Ljava/net/Socket;
    sget-object v3, Lcom/ekyc/digitalsignature/SecurityGuard;->ENC_LOCALHOST:[B
    invoke-static {v3}, Lcom/ekyc/digitalsignature/SecurityGuard;->decryptString([B)Ljava/lang/String;
    move-result-object v3
    const/16 v4, 0x69a2
    invoke-direct {v2, v3, v4}, Ljava/net/Socket;-><init>(Ljava/lang/String;I)V
    invoke-virtual {v2}, Ljava/net/Socket;->close()V
    :try_end_4d
    .catch Ljava/lang/Exception; {:try_start_3b .. :try_end_4d} :catch_4e

    return v0

    :catch_4e
    move-exception v0

    return v1
.end method

# Anti-Debugger Detection
.method public static isDebuggerAttached()Z
    .registers 1
    invoke-static {}, Landroid/os/Debug;->isDebuggerConnected()Z
    move-result v0
    return v0
.end method
