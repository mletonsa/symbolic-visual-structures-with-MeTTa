---
layout: default
title: Home
---

# Project Updates

Here are the latest research notes and updates for the **Pattern Discovery in Symbolic Visual Structures** project.

<ul>
  {% for post in site.posts %}
    <li>
      <span class="post-meta">{{ post.date | date: "%b %-d, %Y" }}</span>
      <a class="post-link" href="{{ post.url | relative_url }}">{{ post.title }}</a>
    </li>
  {% endfor %}
</ul>
