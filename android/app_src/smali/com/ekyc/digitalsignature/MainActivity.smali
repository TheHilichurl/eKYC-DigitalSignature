.class public Lcom/ekyc/digitalsignature/MainActivity;
.super Landroid/app/Activity;
.source "MainActivity.java"

.field private webView:Landroid/webkit/WebView;

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Landroid/app/Activity;-><init>()V
    return-void
.end method

.method protected onCreate(Landroid/os/Bundle;)V
    .registers 6

    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V

    # 1. Anti-Tamper & Security Check on startup
    invoke-static {}, Lcom/ekyc/digitalsignature/SecurityGuard;->isFridaOrHookDetected()Z
    move-result v0
    if-eqz v0, :cond_a

    :cond_a
    # 2. Request Camera permission at runtime (Android 6.0+ / API 23+)
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v1, 0x17
    if-lt v0, v1, :cond_skip_perm

    const/4 v0, 0x1
    new-array v0, v0, [Ljava/lang/String;
    const/4 v1, 0x0
    const-string v2, "android.permission.CAMERA"
    aput-object v2, v0, v1
    const/16 v1, 0x64
    invoke-virtual {p0, v0, v1}, Landroid/app/Activity;->requestPermissions([Ljava/lang/String;I)V

    :cond_skip_perm

    # 3. Create native WebView programmatically
    new-instance v0, Landroid/webkit/WebView;
    invoke-direct {v0, p0}, Landroid/webkit/WebView;-><init>(Landroid/content/Context;)V
    iput-object v0, p0, Lcom/ekyc/digitalsignature/MainActivity;->webView:Landroid/webkit/WebView;

    # 4. Configure WebView Settings
    invoke-virtual {v0}, Landroid/webkit/WebView;->getSettings()Landroid/webkit/WebSettings;
    move-result-object v0
    const/4 v1, 0x1
    invoke-virtual {v0, v1}, Landroid/webkit/WebSettings;->setJavaScriptEnabled(Z)V
    invoke-virtual {v0, v1}, Landroid/webkit/WebSettings;->setDomStorageEnabled(Z)V
    invoke-virtual {v0, v1}, Landroid/webkit/WebSettings;->setAllowFileAccess(Z)V
    const/4 v1, 0x0
    invoke-virtual {v0, v1}, Landroid/webkit/WebSettings;->setMediaPlaybackRequiresUserGesture(Z)V

    # 5. Attach WebAppInterface bridge
    iget-object v0, p0, Lcom/ekyc/digitalsignature/MainActivity;->webView:Landroid/webkit/WebView;
    new-instance v1, Lcom/ekyc/digitalsignature/WebAppInterface;
    invoke-direct {v1, p0}, Lcom/ekyc/digitalsignature/WebAppInterface;-><init>(Landroid/content/Context;)V
    const-string v2, "AndroidBridge"
    invoke-virtual {v0, v1, v2}, Landroid/webkit/WebView;->addJavascriptInterface(Ljava/lang/Object;Ljava/lang/String;)V

    # 6. Attach WebViewClient
    iget-object v0, p0, Lcom/ekyc/digitalsignature/MainActivity;->webView:Landroid/webkit/WebView;
    new-instance v1, Landroid/webkit/WebViewClient;
    invoke-direct {v1}, Landroid/webkit/WebViewClient;-><init>()V
    invoke-virtual {v0, v1}, Landroid/webkit/WebView;->setWebViewClient(Landroid/webkit/WebViewClient;)V

    # 7. Attach WebChromeClient (grant WebRTC / Camera access)
    iget-object v0, p0, Lcom/ekyc/digitalsignature/MainActivity;->webView:Landroid/webkit/WebView;
    new-instance v1, Lcom/ekyc/digitalsignature/AppWebChromeClient;
    invoke-direct {v1}, Lcom/ekyc/digitalsignature/AppWebChromeClient;-><init>()V
    invoke-virtual {v0, v1}, Landroid/webkit/WebView;->setWebChromeClient(Landroid/webkit/WebChromeClient;)V

    # 8. Load URL
    iget-object v0, p0, Lcom/ekyc/digitalsignature/MainActivity;->webView:Landroid/webkit/WebView;
    const-string v1, "file:///android_asset/www/index.html"
    invoke-virtual {v0, v1}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V

    # 9. Set Content View
    iget-object v0, p0, Lcom/ekyc/digitalsignature/MainActivity;->webView:Landroid/webkit/WebView;
    invoke-virtual {p0, v0}, Landroid/app/Activity;->setContentView(Landroid/view/View;)V

    return-void
.end method

.method public onBackPressed()V
    .registers 2
    iget-object v0, p0, Lcom/ekyc/digitalsignature/MainActivity;->webView:Landroid/webkit/WebView;
    if-eqz v0, :cond_13
    invoke-virtual {v0}, Landroid/webkit/WebView;->canGoBack()Z
    move-result v0
    if-eqz v0, :cond_13
    iget-object v0, p0, Lcom/ekyc/digitalsignature/MainActivity;->webView:Landroid/webkit/WebView;
    invoke-virtual {v0}, Landroid/webkit/WebView;->goBack()V
    return-void

    :cond_13
    invoke-super {p0}, Landroid/app/Activity;->onBackPressed()V
    return-void
.end method
