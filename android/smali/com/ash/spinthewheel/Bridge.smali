.class public Lcom/ash/spinthewheel/Bridge;
.super Landroid/webkit/WebChromeClient;

.field private ctx:Landroid/content/Context;

.method public constructor <init>(Landroid/content/Context;)V
    .registers 2
    invoke-direct {p0}, Landroid/webkit/WebChromeClient;-><init>()V
    iput-object p1, p0, Lcom/ash/spinthewheel/Bridge;->ctx:Landroid/content/Context;
    return-void
.end method

# JS calls prompt("vib", "<ms>") to vibrate; any other prompt goes to the default handler.
.method public onJsPrompt(Landroid/webkit/WebView;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Landroid/webkit/JsPromptResult;)Z
    .registers 10
    const-string v0, "vib"
    invoke-virtual {v0, p3}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0
    if-eqz v0, :default

    :try_start
    iget-object v0, p0, Lcom/ash/spinthewheel/Bridge;->ctx:Landroid/content/Context;
    const-string v1, "vibrator"
    invoke-virtual {v0, v1}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;
    move-result-object v0
    check-cast v0, Landroid/os/Vibrator;
    if-eqz v0, :done
    invoke-static {p4}, Ljava/lang/Long;->parseLong(Ljava/lang/String;)J
    move-result-wide v2
    invoke-virtual {v0, v2, v3}, Landroid/os/Vibrator;->vibrate(J)V
    :try_end
    .catch Ljava/lang/Throwable; {:try_start .. :try_end} :done

    :done
    invoke-virtual {p5}, Landroid/webkit/JsPromptResult;->confirm()V
    const/4 v0, 0x1
    return v0

    :default
    invoke-super/range {p0 .. p5}, Landroid/webkit/WebChromeClient;->onJsPrompt(Landroid/webkit/WebView;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Landroid/webkit/JsPromptResult;)Z
    move-result v0
    return v0
.end method
