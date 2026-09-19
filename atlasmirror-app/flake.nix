{
  description = "AtlasMirror: Logos Basecamp QML Application";

  inputs = {
    logos-module-builder.url = "github:logos-co/logos-module-builder/0c5b062fd11b20f85cc7c0720ddcac1cbbb46c4c";
    atlasmirror_sdk.url = "path:../atlasmirror-sdk";
  };

  outputs = inputs@{ logos-module-builder, ... }:
    logos-module-builder.lib.mkLogosQmlModule {
      src = ./.;
      configFile = ./metadata.json;
      flakeInputs = inputs;
    };
}
