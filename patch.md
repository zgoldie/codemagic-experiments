# Cover

## From CodePush to Patch

We have built a successor to CodePush with much needed improvements. Here's what existing users need to know about the migration.


---

# Why we're doing it

After hosting a CodePush fork for two years, we figured it was time for an overhaul

## Dated architecture

Microsoft created CodePush ten years ago. It has been great for the community, but the architecture decisions meant it is painful to host for large volumes of users.

## Missing features

CodePush was missing a good dashboard, native fingerprinting and binary diffs. It was cleaner to add these into a new product than wedge them into CodePush.

---

# Watch the demo

To see Patch in action and how it improves on CodePush, check out this demo

[embed: https://youtu.be/P7628reV_2Y?si=A44py2Nv-fmnItQX]

---

# What's needed to switch

We are trying to make it minimally painful to make the switch.

## Similar SDK and CLI

The SDK and CLI need replacing are similar to CodePush, such as the `sync()` options and `release-react` commands.

## We copy your setup

Patch uses apps and deployments, equivalent to CodePush. We can migrate your setup across into a new Patch account.

## Ship one native binary

The Patch client has to go out through the store or your internal channel. An over-the-air update cannot install the new SDK.

---

# When and how much

We plan to sunset CodePush in six months, so are starting to set up existing customers on Patch. Existing contracts and pricing stand through that window.

---

# Next steps

Our team are here to discuss your OTA setup and moving you across to Patch.

[Book a call](https://codemagic.io/contact)
