{
  description = "AtlasMirror SDK: Logos Core module for OSM snapshot distribution";

  inputs = {
    logos-module-builder.url = "github:logos-co/logos-module-builder/0c5b062fd11b20f85cc7c0720ddcac1cbbb46c4c";
  };

  outputs = inputs@{ logos-module-builder, ... }:
    logos-module-builder.lib.mkLogosModule {
      src = ./.;
      configFile = ./metadata.json;
      flakeInputs = inputs;
    };
}
