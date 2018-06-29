SDK_VERSION=26

export CLASSPATH=${HOME}/Library/Android/sdk/platforms/android-${SDK_VERSION}/android.jar

BUILD_TOOLS_VERSION=26.0.2

export DEX_PATH=${HOME}/Library/Android/sdk/build-tools/${BUILD_TOOLS_VERSION}/lib

make
