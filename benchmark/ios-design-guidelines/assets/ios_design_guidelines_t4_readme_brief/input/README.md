# Fruta：使用 SwiftUI 构建功能丰富的应用程序

创建共享代码库以构建提供小部件和 App Clip 的多平台应用程序。


## 概述

- 注意：此示例项目与 WWDC 2021 会议相关联 [10107: Platforms State of the Union](https://developer.apple.com/wwdc21/10107/)、[10012: What's New in App Clips](https://  /developer.apple.com/wwdc21/10012/), [10013: 构建轻量和快速的应用程序剪辑](https://developer.apple.com/wwdc21/10013/), [10220: 本地化您的 SwiftUI 应用程序](https  ://developer.apple.com/wwdc21/10220/）。

    它还与 WWDC 2020 会议 [10637: Platforms State of the Union](https://developer.apple.com/wwdc20/10637/)、[10146: Configure and Link Your App Clips](https://developer.  apple.com/wwdc20/10146/)、[10120：简化您的 App Clip](https://developer.apple.com/wwdc20/10120/)、[10118：为其他企业创建 App Clip](https://  developer.apple.com/wwdc20/10118/)，[10096：使用 Xcode Playgrounds 探索包和项目](https://developer.apple.com/wwdc20/10096/)，和 [10028：认识 WidgetKit](https:  //developer.apple.com/wwdc20/10028/)。

Fruta 示例应用程序为 macOS、iOS 和 iPadOS 构建了一个应用程序，它实现了 [SwiftUI](https://developer.apple.com/documentation/swiftui) 平台功能，例如小部件、App Clips 和本地化。 用户可以用英语和俄语订购冰沙、保存最喜欢的饮料、收集奖励以及浏览食谱。

示例应用程序的 Xcode 项目包括小部件扩展，使用户能够将小部件添加到他们的 iOS 主屏幕或 macOS 通知中心，并查看他们的奖励或最喜欢的冰沙。  Xcode 项目还包括一个 App Clip 目标。 使用 App Clip，用户可以在 iPhone 或 iPad 上发现并立即启动该应用的某些功能，而无需安装完整的应用。

Fruta 示例应用程序利用 [Sign in with Apple](https://developer.apple.com/documentation/sign_in_with_apple) 和 [Apple Pay](https://developer.apple.com/documentation/passkit) 提供简化的 用户体验。

## 配置示例代码项目

要为 iOS 15 构建此项目，请使用 Xcode 13。运行时要求是 iOS 15。要为 macOS 12 Monterey beta 7 构建此项目，请使用 Xcode 13 beta 5。要配置此项目，请执行以下步骤：

1. 要在您的设备（包括 macOS）上运行，请在目标的签名和功能窗格中设置您的团队。  Xcode 为您管理配置文件。
2. 要在 iOS 或 iPadOS 设备上运行，请打开 `iOSClip.entitlements` 文件并更新 [Parent Application Identifiers Entitlement](https://developer.apple.com/documentation/bundleresources/entitlements/com_apple_developer_parent-application-  identifiers) 以匹配 iOS 应用程序的包标识符。
3. 记下项目设置中 iOS 目标的 Signing & Capabilities 选项卡上的 App Group 名称。 用这个值替换 `Model.swift` 文件中的 group.example.fruta。
4. 要启用应用内购买流程，请编辑 Fruta iOS “运行”方案，并为 StoreKit 配置选择 `Configuration.storekit`。

## 在 SwiftUI 中创建共享代码库

为了创建适用于多个平台的单个应用程序定义，项目定义了一个结构，该结构符合 [App](https://developer.apple.com/documentation/swiftui/app) 协议。 因为 `@main` 属性在结构定义之前，系统将结构识别为应用程序的入口点。 其计算出的 body 属性返回一个 [WindowGroup](https://developer.apple.com/documentation/swiftui/windowgroup) 包含应用程序向用户显示的视图层次结构的场景。  SwiftUI 以适合平台的方式管理场景及其内容的呈现。

``` swift
@main
struct FrutaApp: App {
    @StateObject private var model = Model()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(model)
        }
        .commands {
            SidebarCommands()
            SmoothieCommands(model: model)
        }
    }
}
```
[View in Source](x-source-tag://SingleAppDefinitionTag)

有关更多信息，请参阅 [App 结构和行为](https://developer.apple.com/documentation/swiftui/app-structure-and-behavior)。

## 提供 App Clip 

在 iOS 和 iPadOS 上，Fruta 应用程序为没有将完整应用程序安装为 App Clip 的用户提供部分功能。 该应用程序的 Xcode 项目包含一个 App Clip 目标，并且不会重复代码，而是重用跨所有平台共享的代码来构建 App Clip。 在共享代码中，该项目利用 Active Compilation Condition 构建设置来排除未定义 `APPCLIP` 值的目标的代码。 例如，只有 App Clip 目标呈现 App Store 叠加层以提示用户获取完整的应用程序。

``` swift

VStack(spacing: 0) {
    Spacer()
    
    orderStatusCard
    
    Spacer()
    
    if presentingBottomBanner {
        bottomBanner
    }
    
    #if APPCLIP
    Text(verbatim: "App Store Overlay")
        .hidden()
        .appStoreOverlay(isPresented: $presentingAppStoreOverlay) {
            SKOverlay.AppClipConfiguration(position: .bottom)
        }
    #endif
}
.onChange(of: model.hasAccount) { _ in
    #if APPCLIP
    if model.hasAccount {
        presentingAppStoreOverlay = true
    }
    #endif
}
```
[View in Source](x-source-tag://ActiveCompilationConditionTag)

有关更多信息，请参阅 [使用 Xcode 创建 App Clip](https://developer.apple.com/documentation/app_clips/creating_an_app_clip_with_xcode) 和 [为您的 App Clip 选择正确的功能](https://developer.apple.  com/documentation/app_clips/choosing_the_right_functionality_for_your_app_clip）。

## 创建小部件

为了允许用户在他们的 iOS 主屏幕或 macOS 通知中心中以小部件的形式查看应用程序的一些内容，Xcode 项目包含小部件扩展的目标。 两者都使用在所有目标之间共享的代码。

有关详细信息，请参阅 [WidgetKit](https://developer.apple.com/documentation/widgetkit)。
