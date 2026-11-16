.class public Lcom/ekyc/digitalsignature/WebAppInterface;
.super Ljava/lang/Object;
.source "WebAppInterface.java"

.field private mContext:Landroid/content/Context;

.method public constructor <init>(Landroid/content/Context;)V
    .registers 2
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/ekyc/digitalsignature/WebAppInterface;->mContext:Landroid/content/Context;
    return-void
.end method

# JavascriptInterface annotation
.method public checkSecurityStatus()Ljava/lang/String;
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation
    .registers 4

    invoke-static {}, Lcom/ekyc/digitalsignature/SecurityGuard;->isFridaOrHookDetected()Z
    move-result v0

    invoke-static {}, Lcom/ekyc/digitalsignature/SecurityGuard;->isRooted()Z
    move-result v1

    new-instance v2, Ljava/lang/StringBuilder;
    invoke-direct {v2}, Ljava/lang/StringBuilder;-><init>()V
    const-string v3, "{\"frida\":"
    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    if-nez v0, :cond_1e
    const-string v0, "false"
    goto :goto_20
    :cond_1e
    const-string v0, "true"
    :goto_20
    invoke-virtual {v2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    const-string v0, ",\"root\":"
    invoke-virtual {v2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    if-nez v1, :cond_2e
    const-string v0, "false"
    goto :goto_30
    :cond_2e
    const-string v0, "true"
    :goto_30
    invoke-virtual {v2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v0, "}"
    invoke-virtual {v2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method

.method public detectFace(Ljava/lang/String;)Ljava/lang/String;
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation
    .registers 3
    invoke-static {p1}, Lcom/ekyc/digitalsignature/FaceEngine;->detectFace(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method

.method public signDocument(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation
    .registers 6

    # Security Gate: block if Frida or Root is detected!
    invoke-static {}, Lcom/ekyc/digitalsignature/SecurityGuard;->isFridaOrHookDetected()Z
    move-result v0
    if-eqz v0, :cond_9
    const-string v0, "LỖI BẢO MẬT: Phát hiện công cụ hooking/can thiệp bộ nhớ (Frida)! Từ chối ký số."
    return-object v0

    :cond_9
    # Generate RSA-2048 keypair
    invoke-static {}, Lcom/ekyc/digitalsignature/CryptoEngine;->generateRsaKeyPair()Ljava/security/KeyPair;
    move-result-object v0

    if-nez v0, :cond_12
    const-string v0, "Lỗi khởi tạo module mật mã RSA-2048 trên Android."
    return-object v0

    :cond_12
    new-instance v1, Ljava/lang/StringBuilder;
    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V
    const-string v2, "KÝ SỐ NATIVE THÀNH CÔNG! [Người ký: "
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v1, p2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v2, " | RSA-2048 / SHA256withRSA | Khóa bảo mật phần cứng]"
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method

