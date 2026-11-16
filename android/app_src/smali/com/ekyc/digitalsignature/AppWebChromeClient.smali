.class public Lcom/ekyc/digitalsignature/AppWebChromeClient;
.super Landroid/webkit/WebChromeClient;
.source "AppWebChromeClient.java"

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Landroid/webkit/WebChromeClient;-><init>()V
    return-void
.end method

# Grants camera and microphone access to HTML5/WebRTC
.method public onPermissionRequest(Landroid/webkit/PermissionRequest;)V
    .registers 3
    if-eqz p1, :cond_9
    invoke-virtual {p1}, Landroid/webkit/PermissionRequest;->getResources()[Ljava/lang/String;
    move-result-object v0
    invoke-virtual {p1, v0}, Landroid/webkit/PermissionRequest;->grant([Ljava/lang/String;)V
    :cond_9
    return-void
.end method

