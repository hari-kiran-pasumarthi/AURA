import { AppRegistry } from "react-native";
import App from "./App";
import { name as appName } from "./app.json";
import { createRoot } from "react-dom/client";

AppRegistry.registerComponent(appName, () => App);

const rootTag = document.getElementById("root") || document.getElementById(appName);
const Root = AppRegistry.getRunnable(appName).component;

createRoot(rootTag).render(<Root />);
