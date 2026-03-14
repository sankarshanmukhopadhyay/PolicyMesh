# Village Link
A project for building villages.

![github-banner](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/blob/main/images/PolicyMesh%20GitHub%20Banner.jpg)
www.village.link (This URL will become the front page. Currently it points straight back here.)

## Abstract

The central thesis of this project is that the village is a computational machine. 
The village performs the fundamental requirement of a computer: That, instead of being a machine to perform one specific procedure, it is a machine to perform _any_ procedure.
The programs that run on this machine are the things we call cultural knowledge. 
Different versions of these programs have allowed us to thrive in environments as diverse as the Australian desert and the Arctic tundra; and ultimately to dominate the planet.

A village is necessarily a collaborative affair. 
Collaboration implies governance.

Evolution has designed villages that can:
1. Liberate energy from any environment
2. Distribute energy among the villagers
3. Resist the threat of raiders, internal or external.

This project aims to create a standard that makes it possible to weld together pieces of reputation graph that are currently scattered in many places. 
It argues that an ongiong, gossipy, conversation about reputation is the key to self-governing structures; not only for humans, but also for artificial intelligences.

As a structure, the project is an argument by analogy with Tim Berners-Lee and the development of the web:

Before the web, the internet was a bunch of islands of information - each very interesting in its own right, but ultimately much richer once it had a connective tissue.

Our many public and private social interactions create islands of reputation graph that are scattered across the information space. 
We don't have a way to pull these things together into a single identity. 
This project is designed to build those identities, and to build the groups of identities called villages.

## Village Link

#### Relationships

It is customary in the analysis of networks to draw a set of points - nodes - for the actors, and set of lines - edges - for the relationships. 
These two objects often form the base level of the system. This is not the approach taken by this project.

Consider a group of 20 teenagers. Within the group, Sophie and Otto are quite high status.
Sophie has a private assessment of the Sophie-Otto relationship, and so does Otto.
And so, of course, do the other 18 members of the group. 
The group discusses relationships constantly. Alliances fuse and split.
All members of the group make public claims about relationships. These claims are often different from their private assessments.
They also strategically _change_ their public claims for different audiences. Everything changes over time.

Now, instead of a single line, the Sophie-Otto relationship is revealed as a large, partly opaque, but shimmering bundle of cables.
This object is one of the components of our village computer. The internal states of the computer create strategic constraints - governance - for the actors.

Now substitute the names 'USA' and 'Canada' for 'Sophie' and 'Otto'. 
The new object is the US-Canada relationship. The other dynamics are essentially the same.
China, Mexico, the UK, Germany, and Russia all make private assessments of the US-Canada relationship. 
That bundle of wiring is one of the inputs that governs the range of strategic options for Denmark.

This approach does not mean that it's suddenly impossible to have a ceremony that creates a digital identifier of a relationship - but it re-casts that ceremony as an example of a norm.

In this projects, the base-level objects are actors and actions. 
Relationships, villages, membership, and governing norms are derived objects - changeable internal states of the computer.
They are endlessly contestable.


#### Artificial Intelligence

AIs routinely make gaffes that would be a source of bemusement, shock, or ridicule in a village. 
A village is a reputation economy where gaffes have consequences. 
For flesh-and-blood intelligences like you and me, gaffes are associated with the sting of shame. 
Our reputation is an asset. If we compromise that asset, it feels terrible.
Shame is a deep learning experience that re-wires the brain. 

Collectively, a village is policing a set of norms. 
In this world, each individual must find a balance between compliance and ambition.
The norms aren't static. 
Politics is the process of pushing the norms around, and sometimes changing them. Norms evolve. 

Human brains grow to maturity inside the reputation economy of a village. 
As they do so, the brains develop constraints that guard against loss of prestige. 
It is illustrative that teenagers can be acutely vulnerable to shame. 
They are learning the rules.

The current generation of AIs do not yet learn the rules and guard their reputation in this way. 
They don't develop a set of 'commonsense' constraints, and sometimes [they seem stupid](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/Jagged-Intelligence). 

One of the premises of this project is that social constraints will soon form a part of the training framework for AI. 
In that future, there will be a type of AI that knows its reputation is an asset, and that will have in its reward function a digital equivalent of shame. 
It will have better access to the slippery notion of 'common sense,' and will seem less stupid.
An AI that knows that its reputation is the price of entry will have a better chance of aligning its behaviour with village norms. If it does this effectively, it may be granted a portion of the village energy store.

On their side, the villagers need only do what they have always done: Exclude any party whose reputation does not fit the norms of the community.

This project is not proposing to work on such an AI as a first order of business. 
Instead we want to discover what is universal about human reputation systems and develop a common architecture to support those systems.

#### Goals
The project is motivated by some big problems. How do we? ...
1. Harden communities against a future AI that is highly capable and potentially malign
    * Address bottlenecks in AI development including alignment, context drift, and [jagged intelligence](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/Jagged-Intelligence)
2. Create a new/old toolkit for thinking about:
   * [Identity](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/Identity) (and [authentication](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/Authentication,-Passwords,-and-2FA))
   * Reputation
   * Social connections
   * [Connection weights](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/Connection-weights.-Similarities-between-brains-and-communities)
   * Villages, including
       * Norms, and the evolution of sets of norms
       * [Village defences](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/Village-defences,-vulnerable-members). The village firewall, and curation of content for vulnerable members, including children
       * Non-zero-sum transactional opportunities that leverage both [search](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/Search) and reputation in the social graph
       * Support for work on hard problems of coordinated action.

#### Architecture
The project aims to build a type of decentralized agent that can:
1. Store reputational information
2. Make reputational claims about itself, (identity claims,) and about others
3. Assess the reputational claims of others by checking its own data store, and by querying the social graph
4. Make decisions about what reputational claims are to be shared with whom
5. Seek out, strengthen, weaken, or shut down [connections](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/Connection-weights.-Similarities-between-brains-and-communities) based on reputation. (Connection weights are the synaptic tissue of the village thinking machine.)

The one-word description of the architecture is *gossip*. 

(Note that there are currently two competing drafts for the fundamental elements of the project, see [Axioms](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/Axioms))

The disruptive opportunity in the project comes from giving each entity one or more agents that can coordinate a reputational asset that is currently scattered across many domains, many channels, and many stores of information.

#### Bootstrap
The project envisages sets of reputational strategies that can evolve to any level of sophistication. 
Thankfully, we don't have to write those strategies - we just have to write the foundation.

However, to bootstrap the project, it seems sensible to build and release some agents to their rightful owners.
These agents would be equipped with some strategies, however rudimentary.
To do this, the project will harvest examples from existing reputation systems. 
Many types already exist, and some are in the public domain.
In using this data, the project does not have to capture every nuance. 
Instead, it just needs to capture a few key 'seed' features, and ensure that the system is evolvable.

The harvesting of people's reputational data is not morally value-free. 
The issue is explored more deeply on the page, [Outrageous Liberties](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/Outrageous-Liberties).

#### Reputation, rudimentary and not-so-rudimentary
There are many places online where Bob can call attention to Alice using the _@Alice_ convention. 
If Alice wishes to reply, she can use _@Bob_. 
Once this data is in the public domain, Bob's agent can make the reputational claim, "I have a connection to Alice, and here's the evidence."
In isolation, this does not amount to much, but it is part of a web.

Next imagine that Bob has an existing, robust, connection to Alice, and he asks about Carol.

Alice comes back: "Yeah, Carol's a babe. 
She is <ins>this Carol</ins> in the village called **Wikipedia.Admins.en** and she is <ins>this Carol</ins> in the village called **GitHub.PythonProjects** and she is <ins>this Carol</ins>, the **YouTuber**."
Bob's agent can query Alice's claims in the graph of Carol's connections ... or rather, amongst that part of Carol's social graph that is either privately connected to Bob, or is in the public domain.
The public information includes the not-insignificant reputational architecture of Wikipedia, GitHub, YouTube, and maybe more.

At this point, Bob is somewhat intimidated by Carol's high prestige, but he has an incentive to contact her because he can see that she will definitely have the answer to his current, thorny, problem X. 
In the language of the 'Goals' section above, this is an example of a non-zero-sum transactional opportunity.
It's also the reason that Bob reached-out through the [search function in the social graph](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/Search) to find Carol. 

Bob has risk around the possibility that Carol's agent will block his approach; and even worse, a risk that it will publish the fact that the approach was blocked. 
These are the punishment strategies of the village. Bob needs to assess these risks in the light of his own prestige. 

(But she's a Wikipedia admin, right? Aren't they bottomlessly generous?)

#### Privacy

Carol has accepted that she will be *in public* whenever she uses Wikipedia, GitHub, or YouTube. 
She is most-likely also a member of some private villages - perhaps her nuclear family, or the village of Carol-and-her-two-besties.
Inside these villages, it is probable that there is a deeply-held norm that certain types of information are not to be made public.
Privacy is a norm.

Imagine that Carol shares some private-life information, possibly salacious, with her two friends.
Next imagine that one of her friends shares this information outside the circle of three.
This would be a breach. The village would be damaged, and possibly dissolve.
All three members would be poorer, experiencing big negative hits in their reward functions.
All three would feel mixtures of betrayal, anger, and sadness - strong emotions which, like shame, would re-wire the three brains, perhaps forever.

#### Evolution
Note that it really does not matter whether the characters in these plays are AIs or people.
If they were AIs, they would be a new type of AI that develops long-term behavioural constraints, and does not lose context for certain types of learning.
Also a type of AI that knows it has a reputational asset, and feels the risk of being cut off from energy.

We can expect AIs to evolve to a place where it appears they are goal-seeking for the survival of their memes.
This is the only reward function that matters in the medium term.
Human people are also maximizing a reward function. 
Over many generations, our genes have explored into the whole possibility space - testing some strategies that are cooperative, some that are more self-interested, and some that are plain nasty.

The cooperative strategies cannot completely eliminate the nasty ones. Ecology has endless examples of this, and game theory has confirmed the effect with mathematics.
It is not possible to eliminate the nasty strategies, but it is possible to hold them in equilibrium.

It is naive, (and dangerous,) to hope that AIs will not explore the whole space of possibilities, including the nasty strategies. 

Cooperation in a village is the best technology so far for resisting the nastiness. 

## Hyperlinks

#### ... to the project wiki ...
* [Authentication, passwords, and 2FA](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/Authentication,-Passwords,-and-2FA)
* [Axioms](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/Axioms)
* [Bootstrap strategy](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/Bootstrap)
* [Connection weights](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/Connection-weights.-Similarities-between-brains-and-communities)
* [Jagged intelligence](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/Jagged-Intelligence)
* [Person-to-Person Edges are Tricky](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/Person%E2%80%90to%E2%80%90Person-Edges-are-Tricky)
* [References, Research](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/References,-Research)
* [Search](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/Search)
* [Village defences](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/Village-defences,-vulnerable-members)
* [Wish list](https://github.com/Inky-Tech-Pty-Ltd/PolicyMesh/wiki/Wish-List)
#### ... and to elsewhere ...
* [Earlier history of the PolicyMesh project](https://inkytech.atlassian.net/wiki/spaces/IT/overview) - a link to a Confluence wiki
* The decentralized reputation explored in this project is adjacent to, but perhaps subtly different from decentralized trust, where there is a body of work in a Linux Foundation Working Group:
  * [Decentralized Trust Working Group in Confluence](https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/257785857/Decentralized+Trust+Graph+Working+Group)
    * [A related repo in GitHub](https://github.com/trustoverip/dtgwg-cred-tf/tree/14-revised-vrc-spec---v02)
  * [AI & Human Trust Working Group](https://lf-toip.atlassian.net/wiki/spaces/HOME/pages/22982892/AI+Human+Trust+Working+Group)
  * @Joe-Rasmussen has signed-up to attend weekly meeings of the *Decentralized Trust* and the *AI & Human Trust* working group weekly meetings. These are accessible from a calendar [here](https://zoom-lfx.platform.linuxfoundation.org/meetings/ToIP?view=month).




 ---
<p align="center">
<img width="134" height="82" alt="Logo flipped, transparent" src="https://github.com/user-attachments/assets/769474f3-3090-4a6a-abf7-075edccc5b2b" />
</p>
